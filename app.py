import streamlit as st
import PyPDF2
import requests
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ── Page Setup 
st.set_page_config(page_title="Document Summarizer", page_icon="📄")
st.title("📄 NLP Document Summarizer")
st.write("Upload a PDF or paste a URL to get a summary using the BART AI model.")

# ── Load Model (cached so it loads only once)
@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
    model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")
    return tokenizer, model

tokenizer, model = load_model()

# ── Helper: Extract text from PDF
def extract_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

# ── Helper: Extract text from URL
def extract_url(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")
    return " ".join(p.get_text() for p in paragraphs).strip()

#  Helper: Summarize text using BART
def summarize(text):
    inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
    output = model.generate(inputs["input_ids"], max_length=150, min_length=50, num_beams=4)
    return tokenizer.decode(output[0], skip_special_tokens=True)

# ── UI: Choose Input Type
option = st.radio("Choose input type:", ["PDF File", "URL"])

text = ""

if option == "PDF File":
    file = st.file_uploader("Upload a PDF", type="pdf")
    if file:
        text = extract_pdf(file)
        st.success("Text extracted from PDF!")

elif option == "URL":
    url = st.text_input("Enter URL:")
    if url:
        text = extract_url(url)
        st.success("Text extracted from URL!")

# ── Show Extracted Text 
if text:
    with st.expander("View extracted text"):
        st.write(text[:2000])

    # ── Summarize 
    if st.button("Generate Summary"):
        with st.spinner("Summarizing..."):
            # Truncate input to 3000 chars so model doesn't get overloaded
            summary = summarize(text[:3000])

        st.subheader("Summary:")
        st.write(summary)

        col1, col2 = st.columns(2)
        col1.metric("Original words", len(text.split()))
        col2.metric("Summary words", len(summary.split()))

        st.download_button("Download Summary", summary, file_name="summary.txt")
