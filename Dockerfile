# Use an official GCC image as the base image
FROM gcc:latest

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy the current directory's content to the container's working directory
COPY . .

# Compile the C++ file (change "your_cpp_file.cpp" to the actual filename)
RUN g++ -o output_file your_cpp_file.cpp

# The command to run the C++ program (change "output_file" to the compiled binary name)
CMD ["./output_file"]
