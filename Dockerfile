FROM ubuntu:20.04

# Install necessary packages
RUN dpkg --add-architecture i386 && \
   apt-get update && \
   apt-get install -y \
   wine32 \
   python3 \
   python3-pip \
   git \
   wget \
   && rm -rf /var/lib/apt/lists/*

# Install PyInstaller and other dependencies
RUN pip3 install pyinstaller

# Copy Python project files into the container
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Entry point to build the Python project into a Windows executable
ENTRYPOINT ["wine", "pyinstaller"]

# Command to create a Windows executable from the main script
CMD ["--onefile", "--add-data", "resources:resources", "main.py"]

