# DeepMark-backend

DeepMark is a robust backend system designed to detect and prevent unauthorized reposts of videos on social media platforms. It leverages advanced technologies including facial recognition, digital watermarking, and metadata encoding to verify content ownership and ensure media integrity across the platform.

## 🔑 Key Features

- **Content Authentication**: Upload and verify video/photo content with multi-layered protection
- **Repost Prevention**: Block unauthorized content sharing through:
  - Invisible watermark detection
  - Encrypted metadata verification
  - Facial recognition hash comparison
- **Secure Data Handling**: SHA256 hash generation for facial feature data
- **Advanced Watermarking**: DWT-based (Discrete Wavelet Transform) watermark embedding and extraction
- **Modern API Architecture**: FastAPI-powered RESTful endpoints with async support
- **Robust Storage Solutions**: PostgreSQL database for metadata and Cloudinary for media files
- **High Performance**: Optimized processing pipeline for real-time content verification

## 🧠 Technical Implementation

### Content Protection Flow

#### For New Uploads:
1. **Face Detection & Hashing**: 
   - Extract facial features using state-of-the-art computer vision
   - Generate a cryptographically secure SHA256 hash
   - Store the hash in the database with ownership information

2. **Metadata Encoding**: 
   - Encode the hash using a user-specific encryption key
   - Embed this data into the video/image metadata securely

3. **Watermarking**: 
   - Apply an invisible watermark using DWT techniques
   - Embed the hash's database ID into the content's frequency domain

#### For Verification (When Content is Reuploaded):
1. Extract and attempt to decode metadata using the user's key
2. If decoding fails, extract and match the watermark
3. Perform face recognition to generate a comparative hash
4. Run database comparisons to determine content originality and ownership

## 📁 Project Structure

```
DeepMark-backend/
├── api.py                  # FastAPI application setup
├── main.py                 # Application entry point
├── database.py             # Database session and initialization
├── hashing.py              # SHA256 cryptographic functions
├── encryption.py           # Secure encoding/decoding logic
├── exception_handlers.py   # Custom error handling
├── models/                 # Data models
│   ├── dtos.py             # Models for taking user inputs
│   ├── schemas.py          # SQLModel database schemas
│   └── security.py         # Pydantic model for environment variables
├── routers/                # API route definitions
│   ├── auth.py             # Authentication endpoints
│   ├── post.py             # Post related endoints
├── services/               # Business logic
│   ├── auth.py             # User authentication
│   ├── post.py             # Post logic 
│   └── process.py          # Processing media
│   └── upload.py           # Cloduinary upload
├── video_module/           # Video processing tools
│   ├── watermark.py        # DWT watermarking
│   └── metadata.py         # Video metadata handling
│   └── analyze.py          # Analyzing video to generate hash
├── dependencies/           # Shared dependencies
│   ├── token.py            # JWT token 
│   └── cloud.py            # Cloudinary dependency
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Cloudinary account
- OpenCV dependencies

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/DeepMark-backend.git
cd DeepMark-backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up the database
alembic upgrade head
```

### Configuration

Create a `.env` file in the project root with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/databasename

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Security
MASTER_KEY=your_master_encryption_key
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=time_in_minutes

```

### Running the Application

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📝 API Documentation

Once the application is running, access the interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`



## 📈 Performance Considerations

- Video processing is resource-intensive; consider implementing queue-based processing
- For high-traffic deployments, implement caching for frequently accessed data
- Consider containerization using Docker for consistent deployment environments


## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.