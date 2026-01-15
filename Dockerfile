EXPOSE 8000
CMD ["sh","-c","uvicorn api:app --host 0.0.0.0 --port 8000"]
