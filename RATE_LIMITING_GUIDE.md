# Rate Limiting and Parallel Processing Guide

This guide explains the new rate limiting and parallel processing features implemented in the Construction Progress Monitoring system, inspired by the [OpenAI Cookbook patterns](https://cookbook.openai.com/examples/how_to_handle_rate_limits).

## 🚀 Features Overview

### 1. Rate Limiting with Exponential Backoff
- **Automatic retry logic** with exponential backoff and random jitter
- **Rate limit detection** for 429 errors and quota exceeded scenarios
- **Configurable delays** between requests to prevent rate limit hits
- **Graceful fallback** when tenacity library is not available

### 2. Parallel Processing for Multiple Images
- **Batch processing** of large image sets into manageable chunks
- **Concurrent API requests** with configurable worker threads
- **Automatic batching** when image count exceeds threshold
- **Result aggregation** from multiple batches into unified analysis

### 3. Advanced Parallel Processor
- **Thread-safe job queue** for managing processing tasks
- **Rate limiter integration** with per-minute and per-day limits
- **Retry mechanism** for failed jobs with configurable attempts
- **Real-time statistics** and progress monitoring

## 📦 Installation

Install the required dependencies:

```bash
pip install -r requirements_rate_limiting.txt
```

Or install individually:

```bash
pip install tenacity openai python-dotenv icecream
```

## 🔧 Configuration

### Basic Rate Limiting

The system automatically applies rate limiting when using the OpenAI provider:

```python
from progress_monitoring import AnalysisConfig, ModelProvider, ConstructionSiteAnalyzer

config = AnalysisConfig(
    model_provider=ModelProvider.OPENAI,
    api_key="your-openai-api-key",
    model_name="gpt-4o-mini",
    max_images_per_request=20
)

analyzer = ConstructionSiteAnalyzer(config)
```

### Custom Batch Configuration

For fine-tuned control over parallel processing:

```python
from progress_monitoring.providers.openai_provider import BatchConfig

# Customize batch processing parameters
custom_config = BatchConfig(
    max_images_per_batch=10,        # Images per API request
    max_concurrent_requests=3,      # Parallel requests
    request_delay_seconds=1.0,      # Delay between requests
    max_retries=6,                  # Retry attempts
    timeout_seconds=60              # Request timeout
)

# Apply to OpenAI provider
if isinstance(analyzer.ai_provider, OpenAIProvider):
    analyzer.ai_provider.set_batch_config(custom_config)
```

## 🎯 Usage Examples

### 1. Basic Rate Limiting Demo

```python
# demo_basic_rate_limiting.py
def demo_basic_rate_limiting():
    config = AnalysisConfig(
        model_provider=ModelProvider.OPENAI,
        api_key=OPENAI_API_KEY,
        model_name="gpt-4o-mini",
        memory_file_path="demo_rate_limit_memory.txt"
    )
    
    analyzer = ConstructionSiteAnalyzer(config)
    
    # Automatically uses rate limiting
    day_report = analyzer.analyze_single_day(image_folder, 3, 5)
    
    # Check rate limit statistics
    stats = analyzer.ai_provider.get_rate_limit_stats()
    print(f"Rate limit stats: {stats}")
```

### 2. Parallel Processing Demo

```python
# demo_parallel_processing.py
def demo_parallel_processing():
    config = AnalysisConfig(
        model_provider=ModelProvider.OPENAI,
        api_key=OPENAI_API_KEY,
        model_name="gpt-4o-mini",
        max_images_per_request=50  # Allow more images for parallel processing
    )
    
    analyzer = ConstructionSiteAnalyzer(config)
    
    # Automatically switches to parallel processing for >15 images
    day_report = analyzer.analyze_single_day(image_folder, 3, 5)
```

### 3. Advanced Parallel Processor

```python
from progress_monitoring.utils import process_images_parallel

def demo_advanced_parallel_processor():
    # Direct use of parallel processor
    analysis_text = process_images_parallel(
        images=prepared_images,
        prompt=test_prompt,
        ai_provider=analyzer.ai_provider,
        config=config,
        max_workers=3,    # Number of worker threads
        batch_size=10     # Images per batch
    )
```

## 🔍 How It Works

### Rate Limiting Flow

1. **Request Preparation**: API request is prepared with images and prompt
2. **Rate Check**: System checks if request can be made without hitting limits
3. **Delay Management**: Automatic delays between requests to stay under limits
4. **Error Detection**: Rate limit errors (429) are automatically detected
5. **Retry Logic**: Exponential backoff with random jitter for retries
6. **Fallback**: Graceful fallback to simple retry if tenacity unavailable

### Parallel Processing Flow

1. **Image Assessment**: System checks number of images to process
2. **Batch Decision**: If >15 images, automatically uses parallel processing
3. **Batch Creation**: Images split into configurable batch sizes
4. **Worker Pool**: Multiple worker threads process batches concurrently
5. **Rate Limiting**: Each worker respects rate limits independently
6. **Result Aggregation**: Results from all batches are combined
7. **Error Handling**: Failed batches are retried with exponential backoff

### Advanced Parallel Processor

1. **Job Queue**: Processing jobs are added to thread-safe queue
2. **Worker Threads**: Multiple workers pull jobs from queue
3. **Rate Limiter**: Each worker checks rate limits before making requests
4. **Retry Logic**: Failed jobs are requeued with increased priority
5. **Statistics**: Real-time tracking of processing statistics
6. **Completion**: System waits for all jobs to complete

## ⚙️ Configuration Options

### BatchConfig Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_images_per_batch` | 10 | Maximum images per API request |
| `max_concurrent_requests` | 3 | Number of parallel API requests |
| `request_delay_seconds` | 1.0 | Delay between requests |
| `max_retries` | 6 | Maximum retry attempts |
| `timeout_seconds` | 60 | Request timeout in seconds |

### Rate Limiter Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `requests_per_minute` | 20 | Maximum requests per minute |
| `requests_per_day` | 1000 | Maximum requests per day |

## 🛠️ Troubleshooting

### Common Issues

1. **Rate Limit Errors Still Occurring**
   - Increase `request_delay_seconds` in BatchConfig
   - Reduce `max_concurrent_requests`
   - Check your OpenAI API quota

2. **Memory Issues with Large Image Sets**
   - Reduce `max_images_per_batch`
   - Process images in smaller chunks
   - Monitor system memory usage

3. **Slow Processing**
   - Increase `max_concurrent_requests` (within rate limits)
   - Reduce `request_delay_seconds` (carefully)
   - Check network connectivity

### Debug Information

Enable detailed logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Check rate limit statistics
stats = analyzer.ai_provider.get_rate_limit_stats()
print(f"Rate limit stats: {stats}")
```

## 📊 Performance Considerations

### Optimal Settings

For different scenarios:

**Conservative (Low API Quota):**
```python
BatchConfig(
    max_images_per_batch=5,
    max_concurrent_requests=1,
    request_delay_seconds=2.0
)
```

**Balanced (Standard Usage):**
```python
BatchConfig(
    max_images_per_batch=10,
    max_concurrent_requests=3,
    request_delay_seconds=1.0
)
```

**Aggressive (High API Quota):**
```python
BatchConfig(
    max_images_per_batch=15,
    max_concurrent_requests=5,
    request_delay_seconds=0.5
)
```

### Monitoring Performance

Track processing statistics:

```python
# Get processing statistics
stats = processor.get_stats()
print(f"Jobs processed: {stats['jobs_processed']}")
print(f"Average processing time: {stats['avg_processing_time']:.2f}s")
print(f"Total elapsed time: {stats['elapsed_time']:.2f}s")
```

## 🔗 References

- [OpenAI Rate Limiting Guide](https://cookbook.openai.com/examples/how_to_handle_rate_limits)
- [OpenAI Parallel Processing Script](https://github.com/openai/openai-cookbook/blob/main/examples/api_request_parallel_processor.py)
- [Tenacity Retry Library](https://tenacity.readthedocs.io/)

## 📝 Example Output

```
🚀 Construction Progress Monitoring - Parallel Processing & Rate Limiting Demo
================================================================================
=== Demo: Basic Rate Limiting ===
✅ Analysis completed successfully!
   Images processed: 6
   Status: success
   Rate limit stats: {'request_count': 2, 'last_request_time': 1703123456.789, 'time_since_last_request': 1.23, 'batch_config': BatchConfig(...)}

=== Demo: Parallel Processing ===
✅ Parallel processing completed!
   Images processed: 25
   Status: success

=== Demo: Custom Batch Configuration ===
✅ Custom batch config applied: BatchConfig(max_images_per_batch=5, max_concurrent_requests=2, request_delay_seconds=2.0, max_retries=3, timeout_seconds=30)
✅ Custom batch processing completed!
   Images processed: 6

=== Demo: Advanced Parallel Processor ===
✅ Advanced parallel processing completed!
   Images processed: 25
   Analysis length: 2847 characters
   Analysis preview: The construction site shows significant progress...

================================================================================
✅ All demos completed!

Key Features Demonstrated:
• Rate limiting with exponential backoff
• Parallel processing of multiple image batches
• Customizable batch configurations
• Automatic fallback to sequential processing
• Comprehensive error handling and retry logic
``` 