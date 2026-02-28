import logging

# Configure the root logger to output to console and a file
logging.basicConfig(
    level=logging.INFO,  # Default level for all loggers
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Output to console (stderr)
        logging.FileHandler("app.log"),  # Output to a file
    ],
)
