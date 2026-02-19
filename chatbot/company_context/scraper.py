# Example using Trafilatura (highly recommended for RAG)
from trafilatura import fetch_url, extract

urls = ['https://directwindows.ca/about-us/', 'https://directwindows.ca/', 'https://directwindows.ca/window-replacement/']
clean_text = ''
for url in urls:

    downloaded = fetch_url(url)
    # extract() removes headers/footers automatically
    clean_text += extract(downloaded, include_links=True, output_format='markdown')

with open("chatbot/company_context/direct_window_replacement_context.txt", 'w', encoding="utf-8") as f:
    f.write(clean_text)
