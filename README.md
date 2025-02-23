## Webhook Dify Plugin

**Author:** perzeuss  
**Version:** 0.2.1
**Type:** Extension  

---

### Description

This project is a Dify Plugin that allows users to trigger Dify applications using webhooks seamlessly. With this plugin, you can effortlessly initiate both chatflows and workflows through HTTP requests. 🚀

### Getting Started

To utilize this plugin, you must define an `api_key` upon installation unless the API key location is set to `none`. This key will authenticate your requests to the Dify webhook endpoints: Chatflow and Workflow.

### Installation

1. **Create Endpoint**:  
   In the Endpoints section, click the "+" icon to create a unique webhook domain. You can choose any name you want. Each endpoint can get its own configuration, such as its own credentials.

2. **Configure API Key**:  
   After installing the plugin, ensure you have set up an API key in your settings, unless using the `none` option for the API key location. For other configurations, this key is necessary for authenticating requests to the endpoints. Follow the input prompts in your preferred language for easy configuration.

3. **Configure API Key Location**:  
   The API key can be passed in multiple ways to ensure compatibility with 3rd party systems that will call your webhook:
   - `X-API-Key` header
   - URL query parameter `difyToken`
   - `none` (no API key required)

4. **Available Endpoints**:  
   You will get two endpoint URLs that you can copy and use:
   - **Chatflow Endpoint**
   - **Workflow Endpoint**

### Usage Guide

#### 🔊 Chatflow Endpoint

Trigger a chatflow by sending a POST request to the chatflow endpoint with the required parameters:

- **URL**: `/chatflow`
- **Method**: `POST`
- **Headers**:  
  - `Content-Type: application/json`
  - If using an API key: `x-api-key: <your_api_key>`
- **Body** (JSON):
  ```json
  {
    "app_id": "chatflow_app_id",
    "query": "Hi",
    "inputs": { "name": "John" },
    "conversation_id": ""
  }
  ```

The response will include the chatflow output if the request is successful.

#### 🔄 Workflow Endpoint

To initiate a workflow, send a POST request to the workflow endpoint:

- **URL**: `/workflow`
- **Method**: `POST`
- **Headers**:  
  - `Content-Type: application/json`
  - If using an API key: `x-api-key: <your_api_key>`
- **Body** (JSON):
  ```json
  {
    "app_id": "workflow_app_id",
    "inputs": { "name": "John" }
  }
  ```

The workflow execution will return a JSON response containing the results.

### Additional Information

- Ensure valid JSON for request bodies to prevent parsing errors.
- Successful requests return a 200 status code. Unauthorized access will return a 403 status code unless API key location is set to `none`.
- Proper error messages are provided for input validation failures with a 400 status code.

Harness the power of Dify by automating your chatflow and workflow triggers efficiently using this webhook plugin! 🎉

### Acknowledgments

A big thank you to the Dify team for providing a fantastic developer experience and tools that made the creation of this plugin possible. This plugin was developed during a beta program, and we appreciate the support and resources that were made available throughout this period. ❤️