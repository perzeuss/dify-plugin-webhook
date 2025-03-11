## Dify Plugin: Webhook 

<div align="center">
  <img src="https://img.shields.io/badge/Plugin%20Type-Extensionl-blue" alt="Plugin Type: Extension">
  <img src="https://img.shields.io/github/v/release/perzeuss/dify-plugin-webhook?label=Version&color=DD7200" alt="Latest Release Version">
  <br>
  <img src="https://img.shields.io/badge/Compatible%20With-Dify%201.0-purple" alt="Compatible With: Dify 1.0.*">
  <a href="https://codecov.io/gh/perzeuss/dify-plugin-webhook">
    <img src="https://codecov.io/gh/perzeuss/dify-plugin-webhook/main/graph/badge.svg" alt="Coverage Status">
  </a>
  <img src="https://img.shields.io/github/license/perzeuss/dify-plugin-webhook?label=License&color=darkgreen" alt="License">
</div>

### 🔍 Description

This project is a Dify Plugin that enables seamless triggering of Dify applications using webhooks. With this plugin, you can effortlessly initiate both chatflows and workflows through HTTP requests from any third-party system. 🚀

### ⭐ GitHub Repository
Star and watch our GitHub repository at https://github.com/perzeuss/dify-plugin-webhook to be notified about new releases! The project is open source, feel free to fork and modify it!

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
   Configure the output data from **workflows**. The webhook can send res.body.data (Output of the End node) as the response body without Dify metadata. By default the response contains metada which could conflict with the requirements of your integration.

8. **Available Endpoints**:  
   You have access to the following endpoint URLs:
   - Dynamic endpoints, exposes all apps in the workspace
     - **Chatflow Endpoint**: `/chatflow/<app_id>`
     - **Workflow Endpoint**: `/workflow/<app_id>`
   - Single app endpoints, exposes only the selected app
     - **Chatflow Endpoint**: `/single-chatflow`
     - **Workflow Endpoint**: `/single-workflow`

### 📘 Usage Guide

#### 🔊 Chatflow Endpoint

Trigger a chatflow by sending a POST request to the chatflow endpoint:

- **URL Without App**: `/chatflow/<app_id>`
- **URL With App**: `/single-chatflow`
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

For endpoints configured with a specific Dify app, use the `/single-chatflow` route. A successful response will include the chatflow output.

#### 🔄 Workflow Endpoint

To initiate a workflow, send a POST request to the workflow endpoint:

- **URL Without App**: `/workflow/<app_id>`
- **URL With App**: `/single-workflow`
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

For endpoints configured with a specific Dify app, use the `/single-workflow` route. The response will contain results from the workflow execution.

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

You can create multiple endpoints with different configurations. For example:

- **Discord Bot Endpoint**: With Discord middleware and public key for signature verification
- **Zapier Integration**: With request payload in json_string variable and res.body.data as output
- **Internal Systems**: With full response data including metadata for token usage tracking

#### Custom Response Formatting

For workflows that need to integrate with systems expecting specific response formats:
1. Enable the toggle for: `Send res.body.data instead of res.body as workflow response.`
2. In your Dify workflow, ensure the End node provides exactly the format expected

### 🔍 Troubleshooting

- Use valid JSON for request bodies to avoid parsing errors.
- Successful requests return a 200 status code. Unauthorized access returns a 403 status code unless API key location is set to `none`.
- Proper error messages are given for input validation failures, returning a 400 status code.

Leverage the power of Dify by automating your chatflow and workflow triggers efficiently using this webhook plugin! 🎉

### 🙏 Acknowledgments

Special thanks to the Dify team for delivering a fantastic developer experience and tools that facilitated the creation of this plugin. The first version of this plugin was developed during a beta program, and we appreciate the support and resources made available throughout the period. ❤️