import streamlit as st
import replicate
import os
from exa_py import Exa
from dotenv import load_dotenv

# Load environment variables (Penting untuk portabilitas)
load_dotenv()

# ================================
# KONFIGURASI
# ================================
REPLICATE_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
EXA_KEY = os.environ.get("EXA_API_KEY")

# Model 8B (Cepat & Hemat)
REPLICATE_MODEL = "meta/meta-llama-3-8b-instruct"

st.set_page_config(page_title="Zee Lite", page_icon="✈️", layout="centered")

# ================================
# UI HEADER
# ================================
st.title("✈️ Zee Lite — Smart Travel Guide")
st.caption("Llama-3-8b (Stable) + Ingatan Konteks + Exa Search | Mode Hemat")
st.info("💡 Tips: Mohon ketik pertanyaan LENGKAP. (Contoh: 'Hotel murah di Bali', bukan 'Hotel'). Beri jeda 5-10 detik antar chat.")

# ================================
# HISTORY
# ================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ================================
# LOGIKA UTAMA (HEMAT)
# ================================
q = st.chat_input("Tanya wisata lengkap...")

if q:
    with st.chat_message("user"):
        st.markdown(q)
    st.session_state.chat_history.append({"role": "user", "content": q})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # --- LANGSUNG SEARCHING ---
        context_text = ""
        sources_text = ""
        
        if EXA_KEY:
            try:
                with st.spinner("🔍 Mencari info..."):
                    exa = Exa(api_key=EXA_KEY)
                    search_results = exa.search_and_contents(q, num_results=3, text=True)
                    
                    if search_results:
                        for res in search_results:
                            context_text += f"Title: {res.title}\nContent: {res.text[:800]}\n\n"
                            sources_text += f"- [{res.title}]({res.url})\n"
                    else:
                        context_text = "Tidak ada info online."
            except Exception as e:
                print(f"Exa Error: {e}")

        # --- ANSWERING ---
        full_prompt = f"""
        Kamu Zee, guide travel asik. Gunakan Bahasa Indonesia.
        Jawab pertanyaan user berdasarkan info berikut:
        
        INFO DARI INTERNET:
        {context_text}
        
        USER: {q}
        
        JAWABAN:
        """

        try:
            full_response = ""
            client = replicate.Client(api_token=REPLICATE_TOKEN)
            
            for item in client.run(REPLICATE_MODEL, input={"prompt": full_prompt, "max_new_tokens": 800}):
                full_response += str(item)
                message_placeholder.markdown(full_response + "▌")
            
            if sources_text:
                full_response += f"\n\n**Sumber:**\n{sources_text}"
                
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            if "429" in str(e):
                err_msg = "⏳ **Sabar ya!** Kita terlalu cepat. Tunggu 10 detik lalu coba lagi."
            else:
                err_msg = f"Error: {e}"
            message_placeholder.error(err_msg)
            full_response = err_msg

    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
