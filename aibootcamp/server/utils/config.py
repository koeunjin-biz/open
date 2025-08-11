import os
import glob
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
import pdfplumber

# .env 파일에서 환경 변수 로드
load_dotenv()


class Settings(BaseSettings):
    # Azure OpenAI 설정
    AOAI_API_KEY: str
    AOAI_ENDPOINT: str
    AOAI_DEPLOY_GPT4O: str
    AOAI_EMBEDDING_DEPLOYMENT: str
    AOAI_API_VERSION: str

    # Langfuse 설정
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_HOST: str

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "IPO Advisory Consultant API"

    API_BASE_URL: str

    # SQLite 데이터베이스 설정
    DB_PATH: str = "history.db"
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///./{DB_PATH}"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    SERVER_PORT: int = 8081

    def get_llm(self):
        """Azure OpenAI LLM 인스턴스를 반환합니다."""
        return AzureChatOpenAI(
            openai_api_key=self.AOAI_API_KEY,
            azure_endpoint=self.AOAI_ENDPOINT,
            azure_deployment=self.AOAI_DEPLOY_GPT4O,
            api_version=self.AOAI_API_VERSION,
            temperature=0.7,
            streaming=True,  # 스트리밍 활성화
        )
    

    def get_embeddings(self):
        """Azure OpenAI Embeddings 인스턴스를 반환합니다."""
        return AzureOpenAIEmbeddings(
            model=self.AOAI_EMBEDDING_DEPLOYMENT,
            openai_api_version=self.AOAI_API_VERSION,
            api_key=self.AOAI_API_KEY,
            azure_endpoint=self.AOAI_ENDPOINT,
        )


# 설정 인스턴스 생성
settings = Settings()


# 편의를 위한 함수들, 하위 호환성을 위해 유지
def get_llm():
    return settings.get_llm()


def get_embeddings():
    return settings.get_embeddings()







#------------------------------------------------------------
# pdf파일 -> vectorstore

# PDF파일을 읽는다
def extract_tables_from_pdf(file_path):
    table_texts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                formatted_table = "\n".join([
                    "\t".join([
                        str(cell).replace("\n", " ").strip() if cell is not None else ""
                        for cell in row
                    ]) for row in table
                ])
                table_texts.append(formatted_table)
    return table_texts


#pdf_file_path 파일을 vectorsote에 저장한다
def save_vectorstore(pdf_file_path):
    loader = PyMuPDFLoader(pdf_file_path)
    docs = loader.load()

    table_texts = extract_tables_from_pdf(pdf_file_path)
    table_docs = [Document(page_content=t, metadata={"source": "table"}) for t in table_texts]

    all_docs = docs + table_docs

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    split_documents = text_splitter.split_documents(all_docs)
    
    # 중복 제거 및 고유 ID 부여
    unique_documents = []
    seen_contents = set()
    
    for i, doc in enumerate(split_documents):
        # 내용의 해시값으로 중복 체크
        content_hash = hash(doc.page_content[:200])  # 첫 200자로 중복 체크
        
        if content_hash not in seen_contents:
            # 고유한 ID 부여
            doc.metadata["id"] = f"doc_{i}_{content_hash}"
            unique_documents.append(doc)
            seen_contents.add(content_hash)
    
    print(f"원본 문서: {len(split_documents)}개, 중복 제거 후: {len(unique_documents)}개")
    
    embeddings = settings.get_embeddings()
    vectorstore = FAISS.from_documents(documents=unique_documents, embedding=embeddings)
    vectorstore.save_local("./vector_index")

    return vectorstore


def save_multiple_pdfs_vectorstore(pdf_directory: str = "./data"):
    """여러 PDF 파일을 처리하여 벡터 스토어 생성"""
    print(f"[START]save_multiple_pdfs_vectorstore({pdf_directory})")
    

    
    # PDF 파일 목록 가져오기
    pdf_files = glob.glob(os.path.join(pdf_directory, "*.pdf"))
    
    if not pdf_files:
        print(f"PDF 파일을 찾을 수 없습니다: {pdf_directory}")
        return None
    
    print(f"처리할 PDF 파일 {len(pdf_files)}개 발견:")
    for pdf_file in pdf_files:
        print(f"  - {os.path.basename(pdf_file)}")
    
    all_documents = []
    total_original = 0
    
    # 각 PDF 파일 처리
    for pdf_file in pdf_files:
        try:
            print(f"\n처리 중: {os.path.basename(pdf_file)}")
            
            # PDF 로드
            loader = PyMuPDFLoader(pdf_file)
            docs = loader.load()
            
            # 테이블 추출
            table_texts = extract_tables_from_pdf(pdf_file)
            table_docs = [Document(page_content=t, metadata={"source": "table", "file": os.path.basename(pdf_file)}) for t in table_texts]
            
            # 문서 메타데이터에 파일명 추가
            for doc in docs:
                doc.metadata["file"] = os.path.basename(pdf_file)
            
            file_docs = docs + table_docs
            total_original += len(file_docs)
            
            # 텍스트 분할
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
            split_documents = text_splitter.split_documents(file_docs)
            
            all_documents.extend(split_documents)
            
            print(f"  - 원본: {len(file_docs)}개, 분할 후: {len(split_documents)}개")
            
        except Exception as e:
            print(f"  - 오류 발생: {str(e)}")
            continue
    
    if not all_documents:
        print("처리할 문서가 없습니다.")
        return None
    
    print(f"\n전체 문서 처리 완료:")
    print(f"  - 총 원본 문서: {total_original}개")
    print(f"  - 분할 후 문서: {len(all_documents)}개")
    
    # 중복 제거 및 고유 ID 부여
    unique_documents = []
    seen_contents = set()
    
    for i, doc in enumerate(all_documents):
        # 내용의 해시값으로 중복 체크
        content_hash = hash(doc.page_content[:200])
        
        if content_hash not in seen_contents:
            # 고유한 ID 부여
            doc.metadata["id"] = f"doc_{i}_{content_hash}"
            unique_documents.append(doc)
            seen_contents.add(content_hash)
    
    print(f"  - 중복 제거 후: {len(unique_documents)}개")
    
    # 벡터 스토어 생성
    try:
        embeddings = settings.get_embeddings()
        vectorstore = FAISS.from_documents(documents=unique_documents, embedding=embeddings)
        vectorstore.save_local("./vector_index")
        
        print(f"벡터 스토어 생성 완료: {len(unique_documents)}개 문서")
        return vectorstore
        
    except Exception as e:
        print(f"벡터 스토어 생성 실패: {str(e)}")
        return None


# vectorstore정보를 로딩한다
def load_vectorstore():
    embeddings = settings.get_embeddings()
    vectorstore = FAISS.load_local(
        "./vector_index",
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vectorstore
#------------------------------------------------------------
