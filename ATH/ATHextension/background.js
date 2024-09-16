chrome.action.onClicked.addListener((tab) => {
    if (chrome.scripting) {
      // Inject CSS
      chrome.scripting.insertCSS({
        target: { tabId: tab.id },
        files: ['content.css']
      }, () => {
        if (chrome.runtime.lastError) {
          console.error('CSS Injection Error:', chrome.runtime.lastError.message);
        }
      });
  
      // Inject JS
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      }, () => {
        if (chrome.runtime.lastError) {
          console.error('Script Injection Error:', chrome.runtime.lastError.message);
        }
      });
    } else {
      console.error('chrome.scripting is undefined.');
    }
  });
  
  // Listen for messages from content script
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'startDebugging') {
      const tabId = sender.tab.id;
      chrome.debugger.attach({ tabId }, '1.3', () => {
        if (chrome.runtime.lastError) {
          console.error('Debugger Attach Error:', chrome.runtime.lastError.message);
          sendResponse({ success: false });
          return;
        }
        sendResponse({ success: true });
      });
      return true; // Keep the message channel open for sendResponse
    } else if (request.action === 'dispatchKeyEvent') {
      const tabId = sender.tab.id;
      chrome.debugger.sendCommand({ tabId }, 'Input.dispatchKeyEvent', request.event);
    } else if (request.action === 'stopDebugging') {
      const tabId = sender.tab.id;
      chrome.debugger.detach({ tabId }, () => {
        if (chrome.runtime.lastError) {
          console.error('Debugger Detach Error:', chrome.runtime.lastError.message);
        }
      });
    }
  });
  