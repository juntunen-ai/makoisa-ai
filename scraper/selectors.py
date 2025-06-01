"""CSS selectors and constants for S-kaupat scraping."""

# Store page selectors - Updated for actual S-kaupat.fi structure
STORE_TYPE_LINKS_SELECTOR = 'a[href*="/myymalat/"]'
STORE_TYPE_NAME_SELECTOR = 'a[href*="/myymalat/"]'

# Individual store selectors (discovered from actual site)
STORE_CARD_SELECTOR = "a[href*='prisma'], a[href*='s-market'], a[href*='alepa'], a[href*='sale'], a[href*='herkku']"
STORE_NAME_SELECTOR = ".store-name, .location-name, h2, h3"
STORE_ADDRESS_SELECTOR = ".store-address, .address, .location"
STORE_HOURS_SELECTOR = ".store-hours, .hours, .opening-hours"
STORE_SERVICES_SELECTOR = ".store-services, .services"

# Chain-specific store selectors
PRISMA_STORE_SELECTOR = "a[href*='prisma']"
SMARKET_STORE_SELECTOR = "a[href*='s-market']" 
ALEPA_STORE_SELECTOR = "a[href*='alepa']"
SALE_STORE_SELECTOR = "a[href*='sale']"
HERKKU_STORE_SELECTOR = "a[href*='herkku']"

# Store search and filter selectors
SEARCH_INPUT_SELECTOR = "input[type='search']"
REGION_FILTER_SELECTOR = ".region-filter"
STORE_TYPE_FILTER_SELECTOR = ".store-type-filter"

# Pagination selectors
NEXT_PAGE_SELECTOR = ".pagination__next"
PAGINATION_CONTAINER_SELECTOR = ".pagination"

# Product search selectors (if needed)
PRODUCT_SEARCH_SELECTOR = ".product-search"
PRODUCT_CARD_SELECTOR = ".product-card"

# Product page selectors
PRODUCT_NAME_SELECTOR = "h1"
PRODUCT_PRICE_SELECTOR = 'span:has-text("€")'
PRODUCT_DESCRIPTION_SELECTOR = "p"

# API endpoints (discovered during development)
API_BASE_URL = "https://api.s-kaupat.fi"
STORES_API_ENDPOINT = f"{API_BASE_URL}/stores"
PRODUCTS_API_ENDPOINT = f"{API_BASE_URL}/products"

# Request headers to appear more browser-like
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fi-FI,fi;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Rate limiting
MIN_DELAY_SECONDS = 1
MAX_DELAY_SECONDS = 3
MAX_CONCURRENT_REQUESTS = 5

# Base URLs
BASE_URL = "https://www.s-kaupat.fi"
STORES_URL = f"{BASE_URL}/myymalat"  # Correct stores page URL

# Product page selectors
PRODUCT_NAME_SELECTOR = "h1"
PRODUCT_PRICE_SELECTOR = 'span:has-text("€")'
PRODUCT_DESCRIPTION_SELECTOR = "p"

# Product URL patterns
PRODUCT_URL_PATTERN = "/tuote/"
