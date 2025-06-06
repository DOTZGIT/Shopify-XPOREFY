import requests
import json
import os
import pandas as pd
import time
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime

# Shopify API version
API_VERSION = "2025-01"

# 📌 File to save store credentials
STORE_FILE = "stores.json"
ERROR_LOG_FILE = "error_log.txt"
store_credentials = {}

# Display the welcome banner
def display_welcome():
    print("\n" + "=" * 50)
    print(r"""
.·:''''''''''''''''''''''''''''''''''''''''''''''''''''':·.
: :                                                     : :
: :   __  ______   ___  ____ _____ _____ _______   __   : :
: :   \ \/ /  _ \ / _ \|  _ \_   _| ____|  ___\ \ / /   : :
: :    \  /| |_) | | | | |_) || | |  _| | |_   \ V /    : :
: :    /  \|  __/| |_| |  _ < | | | |___|  _|   | |     : :
: :   /_/\_\_|    \___/|_| \_\|_| |_____|_|     |_|     : :
: :                                                     : :
'·:.....................................................:·'  
    """)
    print("🚀 Welcome to HUB - Your Shopify Data Manager 🚀")
    print("=" * 50)

    # Quick How-To Guide
    print("\n📌 HOW TO USE HUB\n")

    print("🔗 Connect Your Store – Select a saved store or add a new one.")
    print("⚙️ Choose Action – Export, Import, or Migrate Shopify data.")
    print("📂 Select Data – Pick what to export (Products, Orders, Blogs, etc.).")
    print("📑 Choose Format – Save as CSV, JSON, or XML.")
    print("🚀 Export & Download – HUB handles everything automatically.\n")
    print("=" * 50)

# Function to fetch store details from Shopify API
def fetch_store_info(api_key, admin_access_token, store_url):
    """Fetch Shopify store details using API key and access token."""
    url = f"https://{store_url}/admin/api/2025-01/shop.json"  # Corrected API URL
    headers = {"X-Shopify-Access-Token": admin_access_token}

    try:
        response = requests.get(url, headers=headers)
        
        # Handle API response errors
        if response.status_code == 200:
            store_data = response.json().get("shop", {})
            return store_data.get("myshopify_domain", ""), store_data.get("name", ""), store_data.get("email", "")
        
        else:
            print(f"\n⚠️ API Error: {response.status_code}")
            print(f"📜 Response: {response.text}")  # Show actual error details
            return None, None, None

    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {str(e)}")
        return None, None, None

# Shopify API endpoints
SHOPIFY_ENDPOINTS = {
    "Products": "products.json",
    "Smart Collections": "smart_collections.json",
    "Custom Collections": "custom_collections.json",
    "Customers": "customers.json",
    "Discounts": "price_rules.json",
    "Draft Orders": "draft_orders.json",
    "Orders": "orders.json",
    "Pages": "pages.json",
    "Blog Posts": "articles.json",
}

# Function to create export folder in current directory
def get_export_folder():
    today_date = datetime.today().strftime('%Y-%m-%d')
    folder = os.path.join(os.getcwd(), f"exported_{today_date}")
    os.makedirs(folder, exist_ok=True)
    return folder

# Function to log errors
def log_error(message):
    """Logs errors to a file with a timestamp."""
    folder = get_export_folder()  # Ensure folder is defined dynamically
    error_log = os.path.join(folder, "error_log.txt")  # Use get_export_folder()
    
    with open(error_log, "a") as f:
        f.write(f"{datetime.now()} - {message}\n")

    print(f"❌ ERROR: {message}")  

    
# Function to save store credentials
def save_store(store):
    stores = load_stores()
    stores[store["store_url"]] = store  # Save using store URL as key
    with open(STORE_FILE, "w") as file:
        json.dump(stores, file, indent=4)

# Function to load saved stores
def load_stores():
    if os.path.exists(STORE_FILE):
        with open(STORE_FILE, "r") as file:
            return json.load(file)
    return {}
    
# Function to setup store credentials
def setup_store():
    global store_credentials
    stores = load_stores()

    if stores:
        print("\n📌 SAVED STORES\n")
    
        for idx, store in enumerate(stores.values(), 1):
            print(f"{idx}️{store['store_name']} ({store['store_url']})")

        choice = input("\n🔹 Select a store (or type 'new' to add a new one): ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(stores):
            store_credentials = list(stores.values())[int(choice) - 1]
            print(f"\n✅ Successfully Connected To: {store_credentials['store_name']} ({store_credentials['store_url']})\n")
            return store_credentials

    print("\n🔹 Enter Shopify API Credentials:")
    store_url = input("🔹 Store Name (e.g., mystore.myshopify.com): ").strip()
    api_key = input("🔹 API Key: ").strip()
    api_secret_key = input("🔹 API Secret Key: ").strip()
    admin_access_token = input("🔹 Admin Access Token: ").strip()

    store_credentials = {
        "store_name": store_url.split(".")[0],
        "store_url": store_url,
        "api_key": api_key,
        "api_secret_key": api_secret_key,
        "admin_access_token": admin_access_token,
    }

    save_store(store_credentials)
    print(f"\n✅ Successfully Connected To: {store_credentials['store_name']} ({store_credentials['store_url']})\n")
    return store_credentials    
    
# Function to ensure store credentials are loaded before any action
def ensure_store_credentials():
    global store_credentials
    if not store_credentials or "store_name" not in store_credentials:
        print("\n🔹 No store connected. Please enter your Shopify store details.\n")
        store_credentials = setup_store()    

# Function to save data in JSON, CSV, or XML format based on user selection
def save_data(data, filename, folder, formats):
    """Save data in JSON, CSV, or XML format based on user selection."""
    
    # Ensure folder exists
    os.makedirs(folder, exist_ok=True)

    if "json" in formats:
        json_path = os.path.join(folder, f"{filename}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    if "csv" in formats and filename in data:
        df = pd.DataFrame(data[filename])
        csv_path = os.path.join(folder, f"{filename}.csv")

        try:
            # Check if the file exists and remove it before writing
            if os.path.exists(csv_path):
                os.remove(csv_path)  # Delete the existing file

            # Save new CSV file
            df.to_csv(csv_path, index=False, encoding="utf-8")
            print(f"✅ CSV file saved: {csv_path}")

        except PermissionError:
            print(f"❌ ERROR: Permission denied while writing to {csv_path}. Close the file and try again.")
            log_error(f"Permission denied: {csv_path}")

    if "xml" in formats:
        root = ET.Element("root")
        for entry in data.get(filename, []):
            item = ET.SubElement(root, filename[:-1])  # Singular form
            for key, value in entry.items():
                ET.SubElement(item, key).text = str(value)
        tree = ET.ElementTree(root)
        xml_path = os.path.join(folder, f"{filename}.xml")
        tree.write(xml_path)

# Function to fetch all blog categories
def fetch_blog_categories(store):
    """Fetches all blog categories from Shopify."""
    url = f"https://{store['store_url']}/admin/api/{API_VERSION}/blogs.json?limit=250"
    headers = {"X-Shopify-Access-Token": store["admin_access_token"]}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("blogs", [])
    else:
        log_error(f"Error fetching blogs: {response.status_code} - {response.text}")
        return []

# Function to extract images from HTML content
def extract_images_from_html(html_content):
    image_urls = []
    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        images = soup.find_all("img")
        for img in images:
            if img.get("src"):
                image_urls.append(img["src"])
    return ", ".join(image_urls) if image_urls else ""

# Function to get the last exported article ID from CSV
def get_last_article_id(csv_path):
    """Retrieves the highest existing article ID to avoid duplicates."""
    if os.path.exists(csv_path):
        try:
            df_existing = pd.read_csv(csv_path)
            if not df_existing.empty:
                return df_existing["id"].max()
        except Exception as e:
            print(f"⚠️ Error reading CSV: {csv_path}, {e}")
    return 0  # Start from the beginning if no records exist

def export_blog_articles(store, formats):
    """Fetch and save blog articles separately for each category."""
    print("\n📂 Fetching blog categories and exporting articles...")

    # API request to get all blogs
    blog_url = f"https://{store['store_url']}/admin/api/{API_VERSION}/blogs.json?limit=250"
    headers = {"X-Shopify-Access-Token": store["admin_access_token"]}

    blog_response = requests.get(blog_url, headers=headers)
    if blog_response.status_code != 200:
        print(f"❌ Error fetching blogs: {blog_response.status_code} - {blog_response.text}")
        return

    blogs = blog_response.json().get("blogs", [])
    if not blogs:
        print("✅ No blogs found in the store.")
        return

    print(f"📂 Found {len(blogs)} blog categories. Fetching articles...")

    folder = get_export_folder()

    for blog in blogs:
        blog_id = blog["id"]
        blog_title = blog["title"].replace(" ", "_").replace("/", "-")
        json_file_path = os.path.join(folder, f"{blog_title}_articles.json")
        csv_file_path = os.path.join(folder, f"{blog_title}_articles.csv")

        print(f"\n🔍 Fetching new articles for blog: {blog_title} (ID: {blog_id})")

        all_articles = []
        since_id = 0  # Fetch all articles from the beginning

        while True:
            article_url = f"https://{store['store_url']}/admin/api/{API_VERSION}/blogs/{blog_id}/articles.json?limit=250&since_id={since_id}"
            article_response = requests.get(article_url, headers=headers)

            if article_response.status_code != 200:
                print(f"⚠️ Failed to fetch articles for blog {blog_title}: {article_response.status_code}")
                break

            articles = article_response.json().get("articles", [])

            if not articles:
                print(f"✅ No more new articles found for blog {blog_title}. Moving to next blog.")
                break

            for article in articles:
                featured_image = article.get("image", {}).get("src", "")
                description_images = extract_images_from_html(article.get("body_html", ""))

                all_articles.append({
                    "id": article["id"],
                    "title": article["title"],
                    "blog_id": blog_id,
                    "handle": article["handle"],
                    "author": article["author"],
                    "created_at": article["created_at"],
                    "updated_at": article["updated_at"],
                    "published_at": article["published_at"],
                    "summary_html": article.get("summary_html", ""),
                    "body_html": article.get("body_html", "").replace("\n", " ").replace(",", " "),
                    "tags": article.get("tags", ""),
                    "template_suffix": article.get("template_suffix", ""),
                    "metafields": json.dumps(article.get("metafields", {})),
                    "featured_image": featured_image,
                    "description_images": description_images,
                })

            since_id = articles[-1]["id"]

        if all_articles:
            # Save JSON if selected
            if "json" in formats:
                with open(json_file_path, "w", encoding="utf-8") as json_file:
                    json.dump(all_articles, json_file, indent=4, ensure_ascii=False)

            # Save CSV if selected
            if "csv" in formats:
                df_new = pd.DataFrame(all_articles)
                df_new.to_csv(csv_file_path, index=False, encoding="utf-8-sig", sep=",")

            print(f"✅ Exported {len(all_articles)} articles for blog {blog_title}.")
        else:
            print(f"✅ No new articles to add for blog {blog_title}.")

    print(f"\n🎉 All blog articles exported successfully to `{folder}`!")
        
# Function to fetch data from Shopify with pagination (auto-fetch)
def fetch_data(endpoint, store, folder, formats=[]):
    """Fetch data from Shopify and save it in chosen formats automatically without manual input."""
    url = f"https://{store['store_url']}/admin/api/{API_VERSION}/{endpoint}?limit=250"
    headers = {"X-Shopify-Access-Token": store["admin_access_token"]}

    all_data = []
    batch = 1

    while url:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 429:
                print("⏳ Rate limit exceeded. Retrying in 5 seconds...")
                time.sleep(5)
                continue
            elif response.status_code == 200:
                data = response.json()
                filename = endpoint.split(".")[0]
                batch_size = len(data.get(filename, []))
                all_data.extend(data.get(filename, []))

                print(f"✅ Fetched {batch_size} records in batch {batch}.")
                batch += 1

                # Check if there is a next page link
                url = response.links.get("next", {}).get("url")
                if not url:
                    print("🚀 All available data has been fetched successfully!")
                    break  # Exit the loop when there's no next page

            else:
                log_error(f"Error fetching {endpoint}: {response.text}")
                break

        except requests.exceptions.RequestException as e:
            log_error(f"API request failed: {str(e)}")
            break

    if all_data:
        save_data({filename: all_data}, filename, folder, formats)
        print(f"✅ Exported {filename.capitalize()} successfully!")


# Function to export Shopify data
def export_shopify_data():
    global store_credentials
    ensure_store_credentials()
    folder = get_export_folder()

    print(f"\n📦 Exporting data for: {store_credentials['store_name']} ({store_credentials['store_url']})\n")

    print("\n📌 SELECT DATA TO EXPORT")
    for idx, key in enumerate(SHOPIFY_ENDPOINTS.keys(), 1):
        print(f"{idx}️{key}")

    selection = input("\n🔹 Enter numbers (comma-separated) for data to export or type 'all' for everything: ").strip().lower()

    if selection == "all":
        selected_data = list(SHOPIFY_ENDPOINTS.keys())
    else:
        selected_keys = [s.strip() for s in selection.split(",")]
        selected_data = [list(SHOPIFY_ENDPOINTS.keys())[int(k) - 1] for k in selected_keys if k.isdigit() and 1 <= int(k) <= len(SHOPIFY_ENDPOINTS)]

    # Ask user for file formats
    print("\n📦 Select file format(s) for export:")
    print("1️ CSV")
    print("2️ JSON")
    print("3️ XML")
    print("4️ All formats")

    format_choice = input("\n🔹 Select formats (comma-separated): ").strip().split(",")

    formats = []
    if "1" in format_choice:
        formats.append("csv")
    if "2" in format_choice:
        formats.append("json")
    if "3" in format_choice:
        formats.append("xml")
    if "4" in format_choice:
        formats = ["csv", "json", "xml"]

    # FIX: Pass formats parameter when exporting blog articles
    if "Blog Posts" in selected_data:
        export_blog_articles(store_credentials, formats)
        selected_data.remove("Blog Posts")

    # Continue exporting other selected data
    for name in selected_data:
        endpoint = SHOPIFY_ENDPOINTS[name]
        fetch_data(endpoint, store_credentials, folder, formats)

    print(f"✅ Shopify export complete!")

# Function to import/migrate data
def import_shopify_data(destination_store):
    print("\n📥 Select data to import/migrate:")
    for idx, key in enumerate(SHOPIFY_ENDPOINTS.keys(), 1):
        print(f"{idx}️⃣ {key}")

    choices = input("\n🔹 Enter numbers (comma-separated) of what you want to import/migrate: ").strip().split(",")

    folder = get_export_folder()

    for choice in choices:
        if choice.isdigit() and 1 <= int(choice) <= len(SHOPIFY_ENDPOINTS):
            key = list(SHOPIFY_ENDPOINTS.keys())[int(choice) - 1]
            endpoint = SHOPIFY_ENDPOINTS[key]

            json_path = os.path.join(folder, f"{endpoint.split('.')[0]}.json")
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    data = json.load(f)
                    send_data(destination_store, endpoint, data)
            else:
                print(f"⚠️ No data found for {key}.")

# Function to send data to Shopify
def send_data(store, endpoint, data):
    url = f"https://{store['store_url']}/admin/api/{API_VERSION}/{endpoint}"
    headers = {"X-Shopify-Access-Token": store["admin_access_token"], "Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in [200, 201]:
            print(f"✅ Successfully imported {endpoint}!")
        else:
            print(f"❌ Error importing {endpoint}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {str(e)}")    

# Function to display main menu
def main_menu():
    while True:
        ensure_store_credentials()  # Ensure store is connected before any action

        print("\n📌 EXPORTIFY MAIN MENU")
        print("1️ Export Shopify Data")
        print("2️ Import Data to Shopify")
        print("3️ Migrate Data to Another Shopify Store")
        print("4️ Exit")

        choice = input("\n🔹 Select an option (1-4): ").strip()

        if choice == "1":
            export_shopify_data()
        elif choice == "2":
            print("\n🔹 Enter Destination Store API Credentials:")
            destination_store = setup_store()
            import_shopify_data(destination_store)
        elif choice == "3":
            print("\n🔹 Enter Destination Store API Credentials:")
            destination_store = setup_store()
            import_shopify_data(destination_store)
        elif choice == "4":
            print("\n🚀 Thank you for using EXPORTIFY! Goodbye! 👋")
            exit()
        else:
            print("⚠️ Invalid choice. Please select a number between 1-4.")
            
# Function to export new data
def export_new_data():
    global export_folder
    export_folder = get_export_folder()

    if not os.path.exists(export_folder):
        os.makedirs(export_folder)

    print("\n✅ Starting a New Export...")
    print(f"📦 Exporting data for: {store_credentials['store_name']} ({store_credentials['store_url']})\n")

# Function to update latest export
def update_latest_export():
    global export_folder
    export_folder = get_export_folder()

    print("\n🔄 Updating Latest Export...")
    print(f"📦 Updating data for: {store_credentials['store_name']} ({store_credentials['store_url']})\n")

# Function to import data to Shopify
def import_data():
    print("\n📥 Importing Data to Shopify...")
    print(f"📦 Importing to: {store_credentials['store_name']} ({store_credentials['store_url']})\n")

# Function to migrate data to another Shopify store
def migrate_data():
    print("\n🔄 Migrating Data to Another Shopify Store...")
    print(f"📦 Source Store: {store_credentials['store_name']} ({store_credentials['store_url']})\n")

# 🚀 Start the script
display_welcome()
setup_store()  # Load or select store
main_menu()