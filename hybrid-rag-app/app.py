import os
import streamlit as st
import nltk
from nltk.tokenize import word_tokenize
import time

# PDF 로딩 & 텍스트 분할
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 검색기 & LLM
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.retrievers import BM25Retriever
from langchain_core.prompts import ChatPromptTemplate

# ===== 기본 설정 =====
PDF_DIR = "pdfs"
os.makedirs(PDF_DIR, exist_ok=True)  # 폴더 없으면 생성

# NLTK 데이터 확인 (없으면 다운로드)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# ===== LLM & 임베딩 모델 정의 (올바른 모델 이름) =====
LLM_MODEL = "qwen3:8b"
EMBED_MODEL = "nomic-embed-text"

llm = OllamaLLM(model=LLM_MODEL)
embeddings = OllamaEmbeddings(model=EMBED_MODEL)

# ===== 프롬프트 템플릿 =====
template = """
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
Question: {question}
Context: {context}
Answer:
"""
prompt = ChatPromptTemplate.from_template(template)

# ===== 함수 정의 =====
# 하이브리드 검색 = 의미 기반 검색 (Dense Retriever) + 키워드 기반 검색 (Sparse Retriever)
# 의미적 유사성과 키워드 정확성을 모두 활용하는 RAG 시스템
class SimpleHybridRetriever:
    """두 검색기 결과를 가중치로 합치는 간단한 하이브리드 검색기"""
    def __init__(self, retrievers, weights=None):
        self.retrievers = retrievers
        self.weights = weights or [0.5, 0.5]

    def invoke(self, query, top_k=5):
        # 각 검색기 결과를 (문서, 점수)로 가져옴
        doc_score_map = {}
        for retriever, weight in zip(self.retrievers, self.weights):
            docs = retriever.invoke(query)  # 검색기가 문서 리스트를 반환한다고 가정
            # 간단한 점수 계산: 순위 기반 가중치 (첫 번째 문서가 가장 높은 점수)
            for rank, doc in enumerate(docs):
                doc_id = doc.page_content  # 문서 내용을 기준으로 중복 확인 (실제로는 메타데이터나 ID 사용 권장)
                score = weight * (1.0 / (rank + 1))  # 단순 순위 점수
                if doc_id in doc_score_map:
                    doc_score_map[doc_id]['score'] += score
                else:
                    doc_score_map[doc_id] = {'doc': doc, 'score': score}
        # 점수 기준 정렬 후 상위 top_k 반환
        sorted_docs = sorted(doc_score_map.values(), key=lambda x: x['score'], reverse=True)
        return [item['doc'] for item in sorted_docs[:top_k]]

def save_uploaded_file(uploaded_file):
    file_path = os.path.join(PDF_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def load_pdf(file_path):
    loader = PDFPlumberLoader(file_path)
    return loader.load()

def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    return splitter.split_documents(documents)

def build_retrievers(chunks):
    print(f"\n[BUILD] Creating vector store with {len(chunks)} chunks...")
    t0 = time.time()
    vector_store = InMemoryVectorStore(embeddings)
    vector_store.add_documents(chunks)
    print(f"[BUILD] Vector store ready in {time.time()-t0:.2f}s")
    
    semantic_retriever = vector_store.as_retriever(search_kwargs={"k": 10})
    bm25_retriever = BM25Retriever.from_documents(chunks, preprocess_func=lambda x: x.split())
    
    hybrid = SimpleHybridRetriever(
        retrievers=[semantic_retriever, bm25_retriever],
        weights=[0.5, 0.5]
    )
    print("[BUILD] Hybrid retriever ready.")
    return hybrid

def answer_question(question, retrieved_docs):
    print(f"\n{'='*50}")
    print(f"[RAG] Received question: {question}")
    print(f"[RAG] Number of retrieved docs: {len(retrieved_docs)}")

    # 각 문서의 내용 일부를 출력 (앞 150자)
    print("[CONTEXT COMPOSITION]")
    for i, doc in enumerate(retrieved_docs):
        snippet = doc.page_content[:150].replace('\n', ' ')  # 줄바꿈 제거
        print(f"  Chunk {i+1}: {snippet}...")
        # (선택) 메타데이터도 보고 싶다면 아래 주석 해제
        # print(f"    Metadata: {doc.metadata}")

    # 실제 context 생성
    start = time.time()
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    print(f"[RAG] Context length: {len(context)} chars (build in {time.time()-start:.2f}s)")

    chain = prompt | llm
    print("[RAG] Invoking LLM (qwen3:8b)...")

    try:
        llm_start = time.time()
        result = chain.invoke({"question": question, "context": context})
        print(f"[RAG] LLM response received in {time.time()-llm_start:.2f}s")
        print(f"[RAG] Answer: {result[:100]}...")
        return result
    except Exception as e:
        print(f"[ERROR] LLM invocation failed: {e}")
        raise

# ===== Streamlit UI =====
st.title("📄 Hybrid RAG with Qwen3 (8B)")
st.caption("Upload a PDF, then ask questions.")

# 파일 업로드
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", accept_multiple_files=False)

if uploaded_file:
    # 파일 저장 & 처리 (세션에 검색기 저장해 반복 작업 방지)
    if "retriever" not in st.session_state or st.session_state.get("file_name") != uploaded_file.name:
        file_path = save_uploaded_file(uploaded_file)
        documents = load_pdf(file_path)
        chunks = split_documents(documents)
        st.session_state.retriever = build_retrievers(chunks)
        st.session_state.file_name = uploaded_file.name
        st.success(f"Processed {uploaded_file.name} – {len(chunks)} chunks ready.")

    # 채팅 입력
    question = st.chat_input("Ask a question about the PDF...")
    if question:
        st.chat_message("user").write(question)
        with st.spinner("Searching & answering..."):
            print(f"\n[USER QUESTION] {question}")
            ret_start = time.time() 
            docs = st.session_state.retriever.invoke(question)
            print(f"[RETRIEVE] Found {len(docs)} docs in {time.time()-ret_start:.2f}s")
            for i, doc in enumerate(docs[:3]):  # 첫 3개 문서 내용 미리보기
                print(f"[RETRIEVE] Doc {i+1}: {doc.page_content[:80]}...")

            answer = answer_question(question, docs)
        st.chat_message("assistant").write(answer)