#include <iostream>
#include <string>
#include <vector>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <curl/curl.h>
#include <openssl/evp.h>
#include <json/json.h>

namespace fs = std::filesystem;

// Base64 encoding function
std::string base64_encode(const std::string& input) {
    BIO *bio, *b64;
    BUF_MEM *bufferPtr;

    b64 = BIO_new(BIO_f_base64());
    bio = BIO_new(BIO_s_mem());
    bio = BIO_push(b64, bio);

    BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL);
    BIO_write(bio, input.c_str(), input.length());
    BIO_flush(bio);
    BIO_get_mem_ptr(bio, &bufferPtr);

    std::string result(bufferPtr->data, bufferPtr->length);
    BIO_free_all(bio);

    return result;
}

// Callback function for cURL responses
size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* output) {
    size_t totalSize = size * nmemb;
    output->append((char*)contents, totalSize);
    return totalSize;
}

class GitHubAPI {
private:
    std::string token;
    std::string username;
    std::string baseURL = "https://api.github.com";
    
    std::string makeRequest(const std::string& url, const std::string& method, 
                           const std::string& data = "") {
        CURL* curl = curl_easy_init();
std::stringstream buffer;
        buffer << file.rdbuf();
        std::string content = buffer.str();
        file.close();
        
        // Base64 encode the content
        std::string encodedContent = base64_encode(content);
        
        // Get filename from path
        fs::path p(filePath);
        std::string fileName = p.filename().string();
        
        // Create JSON payload
        Json::Value root;
        root["message"] = commitMessage;
        root["content"] = encodedContent;
        
        Json::StreamWriterBuilder writer;
        std::string jsonData = Json::writeString(writer, root);
        
        // Make API request
        std::string url = baseURL + "/repos/" + username + "/" + repoName + 
                         "/contents/" + fileName;
        std::string response = makeRequest(url, "PUT", jsonData);
        
        Json::Value responseJson;
        Json::CharReaderBuilder readerBuilder;
        std::istringstream responseStream(response);
        std::string errs;
        
        if (Json::parseFromStream(readerBuilder, responseStream, &responseJson, &errs)) {
            if (responseJson.isMember("content")) {
                std::cout << "File uploaded successfully: " << fileName << std::endl;
                return true;
            }
        }
        
        std::cerr << "Failed to upload file: " << response << std::endl;
        return false;
    }
    
    bool uploadDirectory(const std::string& repoName, const std::string& dirPath,
                        const std::string& commitMessage) {
        int successCount = 0;
        int failCount = 0;
        
        for (const auto& entry : fs::recursive_directory_iterator(dirPath)) {
            if (entry.is_regular_file()) {
                std::string relativePath = fs::relative(entry.path(), dirPath).string();
                std::cout << "Uploading: " << relativePath << "..." << std::endl;
                
                if (uploadFileWithPath(repoName, entry.path().string(), 
                                      relativePath, commitMessage)) {
                    successCount++;
                } else {
                    failCount++;
                }
            }
        }
        
        std::cout << "\nUpload complete!" << std::endl;
        std::cout << "Success: " << successCount << " files" << std::endl;
        std::cout << "Failed: " << failCount << " files" << std::endl;
        
        return failCount == 0;
    }
    
    bool uploadFileWithPath(const std::string& repoName, const std::string& localPath,
                           const std::string& remotePath, const std::string& commitMessage) {
        // Read file content
        std::ifstream file(localPath, std::ios::binary);
        if (!file.is_open()) {
            std::cerr << "Cannot open file: " << localPath << std::endl;
            return false;
        }
        
        std::stringstream buffer;
        buffer << file.rdbuf();
        std::string content = buffer.str();
        file.close();
        
        // Base64 encode
        std::string encodedContent = base64_encode(content);
        
        // Create JSON payload
        Json::Value root;
        root["message"] = commitMessage;
        root["content"] = encodedContent;
        
        Json::StreamWriterBuilder writer;
        std::string jsonData = Json::writeString(writer, root);
        
        // Make API request
        std::string url = baseURL + "/repos/" + username + "/" + repoName + 
                         "/contents/" + remotePath;
        std::string response = makeRequest(url, "PUT", jsonData);
        
        Json::Value responseJson;
        Json::CharReaderBuilder readerBuilder;
        std::istringstream responseStream(response);
        std::string errs;
        
        if (Json::parseFromStream(readerBuilder, responseStream, &responseJson, &errs)) {
            if (responseJson.isMember("content")) {
                return true;
            }
        }
        
        return false;
    }
    
    bool deleteFile(const std::string& repoName, const std::string& filePath,
                   const std::string& commitMessage) {
        // First, get the file SHA
        std::string url = baseURL + "/repos/" + username + "/" + repoName + 
                         "/contents/" + filePath;
        std::string response = makeRequest(url, "GET");
        
        Json::Value responseJson;
        Json::CharReaderBuilder readerBuilder;
        std::istringstream responseStream(response);
        std::string errs;
        
        if (!Json::parseFromStream(readerBuilder, responseStream, &responseJson, &errs)) {
            std::cerr << "Failed to get file info" << std::endl;
            return false;
        }
        
        std::string sha = responseJson["sha"].asString();
        
        // Delete the file
        Json::Value root;
        root["message"] = commitMessage;
        root["sha"] = sha;
        
        Json::StreamWriterBuilder writer;
        std::string jsonData = Json::writeString(writer, root);
        
        response = makeRequest(url, "DELETE", jsonData);
        
        std::cout << "File deleted successfully: " << filePath << std::endl;
        return true;
    }
    
    void listRepositories() {
        std::string url = baseURL + "/user/repos";
        std::string response = makeRequest(url, "GET");
        
        Json::Value responseJson;
        Json::CharReaderBuilder readerBuilder;
        std::istringstream responseStream(response);
        std::string errs;
        
        if (Json::parseFromStream(readerBuilder, responseStream, &responseJson, &errs)) {
            std::cout << "\nYour Repositories:" << std::endl;
            std::cout << "==================" << std::endl;
            
            for (const auto& repo : responseJson) {
                std::cout << "Name: " << repo["name"].asString() << std::endl;
                std::cout << "Description: " << repo["description"].asString() << std::endl;
                std::cout << "URL: " << repo["html_url"].asString() << std::endl;
                std::cout << "Private: " << (repo["private"].asBool() ? "Yes" : "No") << std::endl;
                std::cout << "------------------" << std::endl;
            }
        }
    }
    
    bool getUserInfo() {
        std::string url = baseURL + "/user";
        std::string response = makeRequest(url, "GET");
        
        Json::Value responseJson;
        Json::CharReaderBuilder readerBuilder;
        std::istringstream responseStream(response);
        std::string errs;
        
        if (Json::parseFromStream(readerBuilder, responseStream, &responseJson, &errs)) {
            std::cout << "\nUser Information:" << std::endl;
            std::cout << "Username: " << responseJson["login"].asString() << std::endl;
            std::cout << "Name: " << responseJson["name"].asString() << std::endl;
            std::cout << "Email: " << responseJson["email"].asString() << std::endl;
            std::cout << "Public Repos: " << responseJson["public_repos"].asInt() << std::endl;
            std::cout << "Followers: " << responseJson["followers"].asInt() << std::endl;
            std::cout << "Following: " << responseJson["following"].asInt() << std::endl;
            return true;
        }
        
        return false;
    }
};

class ProjectManager {
private:
    GitHubAPI* api;
    std::string configFile = "github_config.json";
    
    void saveConfig(const std::string& token, const std::string& username) {
        Json::Value root;
        root["token"] = token;
        root["username"] = username;
        
        Json::StreamWriterBuilder writer;
        std::ofstream file(configFile);
        file << Json::writeString(writer, root);
        file.close();
        
        std::cout << "Configuration saved!" << std::endl;
    }
    
    bool loadConfig(std::string& token, std::string& username) {
        std::ifstream file(configFile);
        if (!file.is_open()) {
            return false;
        }
        
        Json::Value root;
        Json::CharReaderBuilder reader;
        std::string errs;
        
        if (Json::parseFromStream(reader, file, &root, &errs)) {
            token = root["token"].asString();
            username = root["username"].asString();
            file.close();
            return true;
        }
        
        file.close();
        return false;
    }

public:
    ProjectManager() : api(nullptr) {}
    
    ~ProjectManager() {
        delete api;
    }
    
    void initialize() {
        std::string token, username;
        
        if (loadConfig(token, username)) {
            std::cout << "Found saved configuration for user: " << username << std::endl;
            std::cout << "Do you want to use it? (y/n): ";
            char choice;
            std::cin >> choice;
            std::cin.ignore();
            
            if (choice != 'y' && choice != 'Y') {
                token = "";
                username = "";
            }
        }
        
        if (token.empty()) {
            std::cout << "Enter your GitHub Personal Access Token: ";
            std::getline(std::cin, token);
            
            std::cout << "Enter your GitHub username: ";
            std::getline(std::cin, username);
            
            saveConfig(token, username);
        }
        
        api = new GitHubAPI(token, username);
        
        if (api->getUserInfo()) {
            std::cout << "\nAuthentication successful!" << std::endl;
        } else {
            std::cerr << "Authentication failed. Please check your token." << std::endl;
            exit(1);
        }
    }
    
    void showMenu() {
        std::cout << "\n========== GitHub Project Manager ==========" << std::endl;
        std::cout << "1. Create new repository" << std::endl;
        std::cout << "2. Upload single file" << std::endl;
        std::cout << "3. Upload entire project directory" << std::endl;
        std::cout << "4. Delete file from repository" << std::endl;
        std::cout << "5. List your repositories" << std::endl;
        std::cout << "6. View user information" << std::endl;
        std::cout << "7. Exit" << std::endl;
        std::cout << "============================================" << std::endl;
        std::cout << "Enter your choice: ";
    }
    
    void run() {
        initialize();
        
        int choice;
        do {
            showMenu();
            std::cin >> choice;
            std::cin.ignore();
            
            switch (choice) {
                case 1: {
                    std::string repoName, description;
                    char isPrivate;
                    
                    std::cout << "Enter repository name: ";
                    std::getline(std::cin, repoName);
                    
                    std::cout << "Enter description: ";
                    std::getline(std::cin, description);
                    
                    std::cout << "Make it private? (y/n): ";
                    std::cin >> isPrivate;
                    std::cin.ignore();
                    
                    api->createRepository(repoName, description, 
                                        (isPrivate == 'y' || isPrivate == 'Y'));
                    break;
                }
                
                case 2: {
                    std::string repoName, filePath, commitMsg;
                    
                    std::cout << "Enter repository name: ";
                    std::getline(std::cin, repoName);
                    
                    std::cout << "Enter file path: ";
                    std::getline(std::cin, filePath);
                    
                    std::cout << "Enter commit message: ";
                    std::getline(std::cin, commitMsg);
                    
                    api->uploadFile(repoName, filePath, commitMsg);
                    break;
                }
                
                case 3: {
                    std::string repoName, dirPath, commitMsg;
                    
                    std::cout << "Enter repository name: ";
                    std::getline(std::cin, repoName);
                    
                    std::cout << "Enter project directory path: ";
                    std::getline(std::cin, dirPath);
                    
                    std::cout << "Enter commit message: ";
                    std::getline(std::cin, commitMsg);
                    
                    api->uploadDirectory(repoName, dirPath, commitMsg);
                    break;
                }
                
                case 4: {
                    std::string repoName, filePath, commitMsg;
                    
                    std::cout << "Enter repository name: ";
                    std::getline(std::cin, repoName);
                    
                    std::cout << "Enter file path to delete: ";
                    std::getline(std::cin, filePath);
                    
                    std::cout << "Enter commit message: ";
                    std::getline(std::cin, commitMsg);
                    
                    api->deleteFile(repoName, filePath, commitMsg);
                    break;
                }
                
                case 5:
                    api->listRepositories();
                    break;
                
                case 6:
                    api->getUserInfo();
                    break;
                
                case 7:
                    std::cout << "Goodbye!" << std::endl;
                    break;
                
                default:
                    std::cout << "Invalid choice. Please try again." << std::endl;
            }
            
        } while (choice != 7);
    }
};

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "   GitHub Project Manager C++ Client   " << std::endl;
    std::cout << "========================================" << std::endl;
    
    ProjectManager manager;
    manager.run();
    
    return 0;
}d::string response;
        
        if (curl) {
            struct curl_slist* headers = nullptr;
            headers = curl_slist_append(headers, ("Authorization: token " + token).c_str());
            headers = curl_slist_append(headers, "User-Agent: CPP-GitHub-Client");
            headers = curl_slist_append(headers, "Accept: application/vnd.github.v3+json");
            headers = curl_slist_append(headers, "Content-Type: application/json");
            
            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
            
            if (method == "POST") {
                curl_easy_setopt(curl, CURLOPT_POSTFIELDS, data.c_str());
            } else if (method == "PUT") {
                curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "PUT");
                curl_easy_setopt(curl, CURLOPT_POSTFIELDS, data.c_str());
            } else if (method == "DELETE") {
                curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "DELETE");
            }
            
            CURLcode res = curl_easy_perform(curl);
            
            if (res != CURLE_OK) {
                std::cerr << "cURL error: " << curl_easy_strerror(res) << std::endl;
            }
            
            curl_slist_free_all(headers);
            curl_easy_cleanup(curl);
        }
        
        return response;
    }

public:
    GitHubAPI(const std::string& _token, const std::string& _username) 
        : token(_token), username(_username) {
        curl_global_init(CURL_GLOBAL_DEFAULT);
    }
    
    ~GitHubAPI() {
        curl_global_cleanup();
    }
    
    bool createRepository(const std::string& repoName, const std::string& description, 
                         bool isPrivate = false) {
        Json::Value root;
        root["name"] = repoName;
        root["description"] = description;
        root["private"] = isPrivate;
        root["auto_init"] = true;
        
        Json::StreamWriterBuilder writer;
        std::string jsonData = Json::writeString(writer, root);
        
        std::string url = baseURL + "/user/repos";
        std::string response = makeRequest(url, "POST", jsonData);
        
        Json::Value responseJson;
        Json::CharReaderBuilder readerBuilder;
        std::istringstream responseStream(response);
        std::string errs;
        
        if (Json::parseFromStream(readerBuilder, responseStream, &responseJson, &errs)) {
            if (responseJson.isMember("id")) {
                std::cout << "Repository created successfully!" << std::endl;
                std::cout << "URL: " << responseJson["html_url"].asString() << std::endl;
                return true;
            }
        }
        
        std::cerr << "Failed to create repository: " << response << std::endl;
        return false;
    }
    
    bool uploadFile(const std::string& repoName, const std::string& filePath, 
                   const std::string& commitMessage) {
        // Read file content
        std::ifstream file(filePath, std::ios::binary);
        if (!file.is_open()) {
            std::cerr << "Cannot open file: " << filePath << std::endl;
            return false;
        }
        
        std::stringstream buffer;
        buffer << file.rdbuf();