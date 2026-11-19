"""
CIFAR-10 download script with retry logic for slow/unstable connections.
Run this BEFORE opening the notebook.
Usage: python download_cifar10.py
"""
import os
import time
import urllib.request
import tarfile
import hashlib

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CIFAR_URL = "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
CIFAR_FILE = os.path.join(DATA_DIR, "cifar-10-python.tar.gz")
CIFAR_MD5 = "c58f30108f718f92721af3b95e74349a"
MAX_RETRIES = 10
CHUNK_SIZE = 8192  # 8KB chunks for slow connections

os.makedirs(DATA_DIR, exist_ok=True)

def get_remote_size():
    """Get the total file size from server."""
    try:
        req = urllib.request.Request(CIFAR_URL, method='HEAD')
        with urllib.request.urlopen(req, timeout=30) as resp:
            return int(resp.headers.get('Content-Length', 0))
    except Exception:
        return 170498071  # known CIFAR-10 size

def download_with_resume(url, filepath, total_size):
    """Download with resume support and retry logic."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Check if partially downloaded
            existing_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            
            if existing_size >= total_size and total_size > 0:
                print(f"File already fully downloaded ({existing_size:,} bytes)")
                return True
            
            # Resume download from where we left off
            req = urllib.request.Request(url)
            if existing_size > 0:
                req.add_header('Range', f'bytes={existing_size}-')
                print(f"Attempt {attempt}/{MAX_RETRIES}: Resuming from {existing_size:,}/{total_size:,} bytes ({existing_size/total_size:.0%})")
            else:
                print(f"Attempt {attempt}/{MAX_RETRIES}: Starting fresh download...")
            
            mode = 'ab' if existing_size > 0 else 'wb'
            
            with urllib.request.urlopen(req, timeout=60) as response:
                with open(filepath, mode) as f:
                    downloaded = existing_size
                    last_print = time.time()
                    while True:
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Print progress every 5 seconds
                        now = time.time()
                        if now - last_print >= 5:
                            pct = downloaded / total_size * 100 if total_size else 0
                            mb = downloaded / 1e6
                            print(f"  ... {mb:.1f} MB / {total_size/1e6:.1f} MB ({pct:.0f}%)")
                            last_print = now
            
            final_size = os.path.getsize(filepath)
            print(f"Download complete! Size: {final_size:,} bytes")
            return True
            
        except (ConnectionResetError, urllib.error.URLError, OSError, TimeoutError) as e:
            print(f"  Connection error on attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                wait = min(30, 5 * attempt)  # Wait longer between retries
                print(f"  Waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                print("All retries exhausted!")
                return False

def verify_md5(filepath, expected_md5):
    """Verify file integrity."""
    print("Verifying file integrity (MD5)...")
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    actual = md5.hexdigest()
    if actual == expected_md5:
        print(f"MD5 OK: {actual}")
        return True
    else:
        print(f"MD5 MISMATCH: expected {expected_md5}, got {actual}")
        return False

def extract_tarfile(filepath, dest):
    """Extract the tar.gz file."""
    print("Extracting CIFAR-10 dataset...")
    with tarfile.open(filepath, 'r:gz') as tar:
        tar.extractall(path=dest)
    print("Extraction complete!")

def main():
    # Check if already extracted
    extracted_dir = os.path.join(DATA_DIR, 'cifar-10-batches-py')
    if os.path.isdir(extracted_dir) and len(os.listdir(extracted_dir)) >= 8:
        print(f"CIFAR-10 already exists at: {extracted_dir}")
        print("Dataset ready! You can run the notebook now.")
        return
    
    total_size = get_remote_size()
    print(f"CIFAR-10 dataset size: {total_size/1e6:.1f} MB")
    print(f"Destination: {os.path.abspath(DATA_DIR)}")
    print("---")
    
    success = download_with_resume(CIFAR_URL, CIFAR_FILE, total_size)
    
    if not success:
        print("\nDownload failed after all retries.")
        print("Try again later when internet is more stable.")
        return
    
    # Verify
    if not verify_md5(CIFAR_FILE, CIFAR_MD5):
        print("File corrupted. Deleting and please re-run this script.")
        os.remove(CIFAR_FILE)
        return
    
    # Extract
    extract_tarfile(CIFAR_FILE, DATA_DIR)
    
    print("\n=== SUCCESS ===")
    print(f"CIFAR-10 extracted to: {os.path.abspath(extracted_dir)}")
    print("You can now run the notebook!")

if __name__ == '__main__':
    main()
