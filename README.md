## Webhook Dify Plugin

**Author:** perzeuss  
**Version:** 0.4.2  
**Type:** Extension  

---

### 🔍 Description

This project is a Dify Plugin that enables seamless triggering of Dify applications using webhooks. With this plugin, you can effortlessly initiate both chatflows and workflows through HTTP requests from any third-party system. 🚀

### ✨ Key Features & Benefits

| Feature | Webhook Plugin | Standard Dify API | Benefit |
|---------|----------------|-------------------|---------|
| **Flexible API Key Location** | Supports header, URL param, or none | Only Authorization header | Compatible with more third-party systems |
| **Custom Endpoints** | Create multiple endpoints with different configs | Limited to standard endpoints | Support different third-party integrations simultaneously |
| **Request Body Handling** | Full body or inputs object only | Fixed schema required | Works with systems that can't match Dify's schema |
| **Raw Data Output** | Optional removal of Dify metadata | Always includes metadata | Clean responses for third-party integrations |
| **Middleware Support** | Extensible with custom middleware | Not available | Add custom validation, or transformations |
| **Discord Integration** | Built-in Discord webhook support | Requires custom implementation | Effortless Discord bot creation |
| **Authentication Options** | Three authentication methods | Fixed authorization | Flexible security model |

## 🚀 Getting Started

### 📦 Installation
Visit the Dify Plugin marketplace, search for the "Webhook" plugin and click the install button. After installation, click on the "Webhook" plugin on the plugins page.

1. **Create Endpoint**:  
   In the Endpoints section, click the "+" icon to create a unique webhook domain. You can choose any name you want. Each endpoint can have its own configuration, such as individualized credentials and request handling.

2. **Configure API Key**:  
   After installing the plugin, ensure you have set up an API key in your settings, unless using the `none` option for the API key location. For other configurations, this key is necessary for authenticating requests.

3. **Configure API Key Location**:  
   The API key can be utilized in various ways for compatibility with 3rd party systems:
   - `X-API-Key` header
   - URL query parameter `difyToken`
   - `none` (no API key required)

4. **Middleware Support**:  
   The plugin supports the use of custom middlewares for request validation, transformations, and more. Built-in support for Discord webhooks is included, and you can add more middleware for other integrations. Please open a GitHub issue before working on custom middlewares - at the moment there is no dedicated middleware api and you might need to modify the main plugin code to support additional middleware features.

5. **Specify Input Handling**:  
   You have the option to specify whether to use `req.body.inputs` or the entire `req.body` for input variables. This flexibility enhances integration with third-party systems that don't support defining the request payload structure required by Dify.

6. **JSON String Input**:  
   Enable this option to automatically convert the entire request body to a JSON string. This is particularly useful when you want to pass a complex payload through a single input variable in Dify and parse it within your application logic.

7. **Specify Output Handling**:  
   Configure how the output data from **workflows** is returned using the `raw_data_output` flag:
   - Set `raw_data_output` to `true` to receive only the output of the End node without Dify metadata.
   - Default setting is `false`, which includes Dify metadata in the response.

   This configuration ensures output data aligns perfectly with the requirements of your integration.

8. **Available Endpoints**:  
   You have access to two endpoint URLs:
   - **Chatflow Endpoint**: `/chatflow/<app_id>`
   - **Workflow Endpoint**: `/workflow/<app_id>`

### 📘 Usage Guide

#### 🔊 Chatflow Endpoint

Trigger a chatflow by sending a POST request to the chatflow endpoint:

- **URL**: `/chatflow/<app_id>`
- **Method**: `POST`
- **Headers**:  
  - `Content-Type: application/json`
  - If using an API key: `X-API-Key: <your_api_key>`
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

To initiate a workflow, send a POST request to the workflow endpoint:

- **URL**: `/workflow/<app_id>`
- **Method**: `POST`
- **Headers**:  
  - `Content-Type: application/json`
  - If using an API key: `X-API-Key: <your_api_key>`
- **Body** (JSON):
  ```json
  {
    "inputs": { "name": "John" }
  }
  ```

The response will contain results from the workflow execution.

### 🧩 Customization with Middlewares

The plugin supports middleware for extended functionality:

1. **Discord Webhook Integration**:  
   Built-in support for Discord interaction verification and response handling.

2. **Default Middleware**:  
   Provides JSON string conversion functionality.

3. **Custom Middlewares**:  
   You can develop additional middlewares to:
   - Verify signatures from other platforms
   - Transform request and response data
   - Implement custom authentication methods
   - Handle special payload formats

### ⚙️ Advanced Configuration Examples

#### Multiple Endpoints Configuration

You can create multiple endpoints with different configurations:

- **Discord Bot Endpoint**: With Discord middleware and no API key
- **Zapier Integration**: With API key in URL parameter and raw data output
- **Internal Systems**: With API key in header and full response data

#### Custom Response Formatting

For workflows that need to integrate with systems expecting specific response formats:
1. Configure the endpoint with `raw_data_output: true`
2. In your Dify workflow, ensure the End node provides exactly the format expected

### 🔍 Troubleshooting

- Use valid JSON for request bodies to avoid parsing errors.
- Successful requests return a 200 status code. Unauthorized access returns a 403 status code unless API key location is set to `none`.
- Proper error messages are given for input validation failures, returning a 400 status code.

Leverage the power of Dify by automating your chatflow and workflow triggers efficiently using this webhook plugin! 🎉

### 🙏 Acknowledgments

Special thanks to the Dify team for delivering a fantastic developer experience and tools that facilitated the creation of this plugin. The first version of this plugin was developed during a beta program, and we appreciate the support and resources made available throughout the period. ❤️