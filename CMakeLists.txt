cmake_minimum_required(VERSION 3.10)
project(GitHubProjectManager)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(CURL REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(jsoncpp REQUIRED)

# Source files
set(SOURCES
    main.cpp
)

# Create executable
add_executable(github_manager ${SOURCES})

# Link libraries
target_link_libraries(github_manager
    PRIVATE
    CURL::libcurl
    OpenSSL::SSL
    OpenSSL::Crypto
    jsoncpp_lib
)

# Include directories
target_include_directories(github_manager
    PRIVATE
    ${CURL_INCLUDE_DIRS}
    ${OPENSSL_INCLUDE_DIR}
)

# Compiler flags
if(MSVC)
    target_compile_options(github_manager PRIVATE /W4)
else()
    target_compile_options(github_manager PRIVATE -Wall -Wextra -pedantic)
endif()

# Installation
install(TARGETS github_manager DESTINATION bin)