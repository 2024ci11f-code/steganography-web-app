import io
from PIL import Image
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Image Steganography Web App", page_icon="🔒", layout="wide"
)

# --- STEGANOGRAPHY CORE LOGIC ---


def text_to_bin(text):
  return "".join(format(ord(char), "08b") for char in text)


def bin_to_text(binary_data):
  bytes_list = [binary_data[i : i + 8] for i in range(0, len(binary_data), 8)]
  decoded = ""
  for byte in bytes_list:
    decoded += chr(int(byte, 2))
  return decoded


def encode_data(image, secret_text):
  img = image.convert("RGB")
  pixels = img.load()
  width, height = img.size

  delimiter = "#####"
  binary_text = text_to_bin(secret_text + delimiter)
  data_len = len(binary_text)

  if data_len > width * height * 3:
    raise ValueError("Text is too long for this image size!")

  idx = 0
  for y in range(height):
    for x in range(width):
      if idx >= data_len:
        break
      r, g, b = pixels[x, y]

      if idx < data_len:
        r = (r & ~1) | int(binary_text[idx])
        idx += 1
      if idx < data_len:
        g = (g & ~1) | int(binary_text[idx])
        idx += 1
      if idx < data_len:
        b = (b & ~1) | int(binary_text[idx])
        idx += 1

      pixels[x, y] = (r, g, b)
    if idx >= data_len:
      break

  output_buffer = io.BytesIO()
  img.save(output_buffer, format="PNG")
  return output_buffer.getvalue()


def decode_data(image):
  img = image.convert("RGB")
  pixels = img.load()
  width, height = img.size

  binary_data = ""
  delimiter = text_to_bin("#####")

  for y in range(height):
    for x in range(width):
      r, g, b = pixels[x, y]
      binary_data += str(r & 1)
      binary_data += str(g & 1)
      binary_data += str(b & 1)

      if delimiter in binary_data:
        secret_bin = binary_data.split(delimiter)[0]
        return bin_to_text(secret_bin)

  return "No hidden message found."


# --- STREAMLIT WEB INTERFACE ---

st.title("🔒 Image Steganography Web Application")
st.markdown(
    "Hide secret messages inside PNG images using the **Least Significant Bit"
    " (LSB)** technique."
)

tab1, tab2 = st.tabs(["🔒 Encode Message", "🔓 Decode Message"])

# TAB 1: ENCODE
with tab1:
  st.header("Encode a Secret Message")
  uploaded_file = st.file_uploader(
      "Upload Cover Image (.png)", type=["png"], key="enc_upload"
  )

  if uploaded_file is not None:
    cover_img = Image.open(uploaded_file)

    col1, col2 = st.columns(2)
    with col1:
      st.image(
          cover_img, caption="Original Cover Image", use_container_width=True
      )

    with col2:
      secret_msg = st.text_area("Enter Secret Message:", height=150)

      if st.button("Encode Message", type="primary"):
        if not secret_msg:
          st.error("Please enter a message to hide!")
        else:
          try:
            stego_bytes = encode_data(cover_img, secret_msg)
            st.success("Message hidden successfully!")

            st.download_button(
                label="⬇️ Download Encoded Stego Image",
                data=stego_bytes,
                file_name="stego_image.png",
                mime="image/png",
            )
          except Exception as e:
            st.error(f"Error: {str(e)}")

# TAB 2: DECODE
with tab2:
  st.header("Decode a Hidden Message")
  stego_file = st.file_uploader(
      "Upload Stego Image (.png)", type=["png"], key="dec_upload"
  )

  if stego_file is not None:
    stego_img = Image.open(stego_file)

    col1, col2 = st.columns(2)
    with col1:
      st.image(
          stego_img, caption="Uploaded Stego Image", use_container_width=True
      )

    with col2:
      if st.button("Extract Hidden Message", type="primary"):
        hidden_text = decode_data(stego_img)
        st.subheader("Extracted Message:")
        st.info(hidden_text)