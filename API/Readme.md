# Micro-Tiling API

This is a wrapper around the microservices to generate a mosaic

# Dependencies

- Flask `pip install flask`

# Usage

Generate a new job with POST `/`
Get the state with GET `/<job_id>/state`
Get the ensicoin address needing fees with GET `/<job_id>/address`
Get the result with GET `/<job_id>/result`
