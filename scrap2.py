import requests
from bs4 import BeautifulSoup

# Replace 'your_url_here' with the actual URL you want to scrape
url = 'your_url_here'

# Send a GET request to the URL
response = requests.get(url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Define a custom filter function to find <span> elements not inside any <div>
    def is_span_without_div(tag):
        return tag.name == 'span' and not tag.find_parent('div') and tag.get('style', '').lower().find('color: red') != -1

    # Find all <span> elements that match the filter function
    red_span_elements = soup.find_all(is_span_without_div)

    # Extract and print the content of each <tr> element containing a red <span>
    for red_span in red_span_elements:
        tr_element = red_span.find_parent('tr')
        if tr_element:
            print(tr_element.text)
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
