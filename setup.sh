mkdir -p ~/.streamlit/
echo "\
[browser]\n\
driver = chrome\n\
[chrome]\n\
executable_path = /app/.chromedriver/bin/chromedriver\n\
" > ~/.streamlit/config.toml
