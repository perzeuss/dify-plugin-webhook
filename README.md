## Webhook Dify Plugin

**Author:** perzeuss  
**Version:** 0.4.0 
**Type:** Extension  

---

### Description

This project is a Dify Plugin that enables seamless triggering of Dify applications using webhooks. With this plugin, you can effortlessly initiate both chatflows and workflows through HTTP requests. 🚀

### Getting Started

To utilize this plugin, you must define an `api_key` unless the API key location is set to `none`. This key authenticates your requests to the Dify webhook endpoints: Chatflow and Workflow.

### Installation

1. **Create Endpoint**:  
   In the Endpoints section, click the "+" icon to create a unique webhook domain. You can choose any name you want. Each endpoint can have its own configuration, such as individualized credentials.

2. **Configure API Key**:  
   After installing the plugin, ensure you have set up an API key in your settings, unless using the `none` option for the API key location. For other configurations, this key is necessary for authenticating requests. Follow the input prompts in your preferred language for easy configuration.

3. **Configure API Key Location**:  
   The API key can be utilized in various ways for compatibility with 3rd party systems:
   - `X-API-Key` header
   - URL query parameter `difyToken`
   - `none` (no API key required)

4. **Middleware Support**:  
   The plugin now supports the use of custom middlewares. Contributors are encouraged to add more middlewares to the collection. Middlewares can be applied for request validation, implementing request mappings, etc.

5. **Specify Input Handling**:  
   You have the option to specify whether to use `req.body.inputs` or the entire `req.body` for input variables. This flexibility enhances integration with third-party systems that don't support defining the request payload.

6. **Specify Output Handling**:  
   You can configure how the output data from **workflows** is returned using the `raw_data_output` flag. This option provides flexibility in determining whether to receive the response as-is or without Dify metadata:
   - Set `raw_data_output` to `true` to receive the output of the End node without Dify metadata.
   - Default setting is `false`, which includes Dify metadata in the response.

   This configuration is particularly useful for workflows to ensure that output data aligns with the requirements of your integration.

7. **Available Endpoints**:  
   You have access to two endpoint URLs:
   - **Chatflow Endpoint**
   - **Workflow Endpoint**

### Usage Guide

#### 🔊 Chatflow Endpoint

Trigger a chatflow by sending a POST request to the chatflow endpoint with the path parameter:

- **URL**: `/chatflow/<app_id>`
- **Method**: `POST`
- **Headers**:  
  - `Content-Type: application/json`
  - If using an API key: `x-api-key: <your_api_key>`
- **Body** (JSON):
  ```json
  {
    "query": "Hi",
    "inputs": { "name": "John" },
    "conversation_id": ""
  }
  ```

A successful response will include the chatflow output.

#### 🔄 Workflow Endpoint

To initiate a workflow, send a POST request to the workflow endpoint with the path parameter:

- **URL**: `/workflow/<app_id>`
- **Method**: `POST`
- **Headers**:  
  - `Content-Type: application/json`
  - If using an API key: `x-api-key: <your_api_key>`
- **Body** (JSON):
  ```json
  {
    "inputs": { "name": "John" }
  }
  ```

The response will contain results from the workflow execution.

### Additional Information

- Use valid JSON for request bodies to avoid parsing errors.
- Successful requests return a 200 status code. Unauthorized access returns a 403 status code unless API key location is set to `none`.
- Proper error messages are given for input validation failures, returning a 400 status code.

Leverage the power of Dify by automating your chatflow and workflow triggers efficiently using this webhook plugin! 🎉

### Acknowledgments

Special thanks to the Dify team for delivering a fantastic developer experience and tools that facilitated the creation of this plugin. This plugin was developed during a beta program, and we appreciate the support and resources made available throughout the period. ❤️