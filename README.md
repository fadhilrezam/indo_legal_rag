# indo_legal_rag

![screenshoot](logo.png)

# Flow Chart
 ```mermaid
flowchart TD
    A[Start] --> B[User Isi Formulir]
    B --> C[Klik Submit Form]
    C --> D{Form Valid?}
    D -->|No| B
    D -->|Yes| E[Masuk ke Chatbot]
    E --> F[User Kirim Pertanyaan]
    F --> G[Bot Jawab via RAG Pipeline]
    G --> H[Jawaban Ditampilkan]
    H --> I{User Mau Bertanya Lagi?}
    I -->|Yes| F
    I -->|No| J[Simpan ke Database]
    J --> K[Akhiri Sesi]
    K --> L[End]

    style A fill:#2196F3,color:#fff
    style E fill:#4CAF50,color:#fff
    style G fill:#FF9800,color:#fff
    style J fill:#9C27B0,color:#fff
    style L fill:#607D8B,color:#fff
```

