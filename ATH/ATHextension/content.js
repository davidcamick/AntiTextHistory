(function() {
    // Check if the UI already exists
    if (document.getElementById('typingSimulatorUI')) {
      return;
    }
  
    // Create the UI container
    const uiContainer = document.createElement('div');
    uiContainer.id = 'typingSimulatorUI';
    uiContainer.innerHTML = `
      <button id="closeButton">&times;</button>
      <h2>Typing Simulator</h2>
      <div id="tabs">
        <button class="tablink" data-tab="TextInput">Text Input</button>
        <button class="tablink" data-tab="SpeedSettings">Speed Settings</button>
        <button class="tablink" data-tab="About">About</button>
      </div>
      <div id="TextInput" class="tabcontent">
        <label for="textInput">Enter the text you want to type:</label>
        <textarea id="textInput"></textarea>
        <button id="startButton">Start Typing</button>
        <p id="status"></p>
        <p id="countdown"></p>
      </div>
      <div id="SpeedSettings" class="tabcontent" style="display:none;">
        <label for="wpmRange">Typing speed (words per minute): <span id="wpmValue">60</span></label>
        <input type="range" id="wpmRange" min="1" max="500" value="60">
        <label><input type="checkbox" id="includePauses"> Include Pauses</label>
        <div id="pausesSettings" style="display:none;">
          <label for="pauseSentenceRange">Pause after sentences (seconds): <span id="pauseSentenceValue">0</span></label>
          <input type="range" id="pauseSentenceRange" min="0" max="10" step="0.1" value="0">
          <label for="pauseParagraphRange">Pause after paragraphs (seconds): <span id="pauseParagraphValue">0</span></label>
          <input type="range" id="pauseParagraphRange" min="0" max="10" step="0.1" value="0">
          <label for="pauseMidSentenceRange">Pause mid-sentence (seconds): <span id="pauseMidSentenceValue">0</span></label>
          <input type="range" id="pauseMidSentenceRange" min="0" max="10" step="0.1" value="0">
          <label for="pauseMinRange">Pause time range minimum (seconds): <span id="pauseMinValue">1</span></label>
          <input type="range" id="pauseMinRange" min="0" max="10" step="0.1" value="1">
          <label for="pauseMaxRange">Pause time range maximum (seconds): <span id="pauseMaxValue">3</span></label>
          <input type="range" id="pauseMaxRange" min="0" max="10" step="0.1" value="3">
        </div>
      </div>
      <div id="About" class="tabcontent" style="display:none;">
        <h2>About Typing Simulator</h2>
        <p>Developed by David Camick with the help of ChatGPT.</p>
        <p>This extension simulates typing text into web pages, making it appear as if it was typed manually.</p>
      </div>
    `;
    document.body.appendChild(uiContainer);
  
    // Add event listeners
    const tabLinks = uiContainer.querySelectorAll('.tablink');
    tabLinks.forEach(function(tabLink) {
      tabLink.addEventListener('click', function(event) {
        const tabName = this.getAttribute('data-tab');
        openTab(tabName);
      });
    });
  
    // Open the first tab by default
    openTab('TextInput');
  
    function openTab(tabName) {
      const tabContents = uiContainer.getElementsByClassName('tabcontent');
      for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = 'none';
      }
  
      const tabLinks = uiContainer.getElementsByClassName('tablink');
      for (let i = 0; i < tabLinks.length; i++) {
        tabLinks[i].style.backgroundColor = '';
        tabLinks[i].style.color = '';
      }
  
      const activeTab = uiContainer.querySelector('#' + tabName);
      if (activeTab) {
        activeTab.style.display = 'block';
      }
  
      const activeButton = uiContainer.querySelector('.tablink[data-tab="' + tabName + '"]');
      if (activeButton) {
        activeButton.style.backgroundColor = '#4A00E0';
        activeButton.style.color = '#FFFFFF';
      }
    }
  
    // Event listeners for UI elements
    const wpmRange = document.getElementById('wpmRange');
    const wpmValue = document.getElementById('wpmValue');
    wpmRange.addEventListener('input', function() {
      wpmValue.innerText = this.value;
    });
  
    const includePausesCheckbox = document.getElementById('includePauses');
    const pausesSettingsDiv = document.getElementById('pausesSettings');
    includePausesCheckbox.addEventListener('change', function() {
      pausesSettingsDiv.style.display = this.checked ? 'block' : 'none';
    });
  
    // Pause settings sliders
    const pauseSentenceRange = document.getElementById('pauseSentenceRange');
    const pauseSentenceValue = document.getElementById('pauseSentenceValue');
    pauseSentenceRange.addEventListener('input', function() {
      pauseSentenceValue.innerText = this.value;
    });
  
    const pauseParagraphRange = document.getElementById('pauseParagraphRange');
    const pauseParagraphValue = document.getElementById('pauseParagraphValue');
    pauseParagraphRange.addEventListener('input', function() {
      pauseParagraphValue.innerText = this.value;
    });
  
    const pauseMidSentenceRange = document.getElementById('pauseMidSentenceRange');
    const pauseMidSentenceValue = document.getElementById('pauseMidSentenceValue');
    pauseMidSentenceRange.addEventListener('input', function() {
      pauseMidSentenceValue.innerText = this.value;
    });
  
    const pauseMinRange = document.getElementById('pauseMinRange');
    const pauseMinValue = document.getElementById('pauseMinValue');
    pauseMinRange.addEventListener('input', function() {
      pauseMinValue.innerText = this.value;
    });
  
    const pauseMaxRange = document.getElementById('pauseMaxRange');
    const pauseMaxValue = document.getElementById('pauseMaxValue');
    pauseMaxRange.addEventListener('input', function() {
      pauseMaxValue.innerText = this.value;
    });
  
    const startButton = document.getElementById('startButton');
    const countdownDisplay = document.getElementById('countdown');
    startButton.addEventListener('click', function() {
      const text = document.getElementById('textInput').value;
      if (!text.trim()) {
        alert('Please enter the text you want to type.');
        return;
      }
  
      const wpm = parseInt(wpmRange.value);
  
      // Pause settings
      const includePauses = includePausesCheckbox.checked;
      let pauses = {};
      if (includePauses) {
        pauses = {
          pauseSentence: parseFloat(pauseSentenceRange.value) || 0,
          pauseParagraph: parseFloat(pauseParagraphRange.value) || 0,
          pauseMidSentence: parseFloat(pauseMidSentenceRange.value) || 0,
          pauseMin: parseFloat(pauseMinRange.value) || 0,
          pauseMax: parseFloat(pauseMaxRange.value) || 0
        };
        if (pauses.pauseMin > pauses.pauseMax) {
          alert('Minimum pause time cannot be greater than maximum pause time.');
          return;
        }
      }
  
      // Show estimated time before starting
      const estimatedTime = calculateEstimatedTime(text, wpm, pauses, includePauses);
      if (!confirm(`Estimated time for completion is: ${estimatedTime.toFixed(2)} seconds.\nDo you want to proceed?`)) {
        return;
      }
  
      // Start 5-second countdown
      let countdown = 5;
      countdownDisplay.innerText = `You have ${countdown} seconds to focus on the target text field...`;
      const countdownInterval = setInterval(() => {
        countdown--;
        if (countdown > 0) {
          countdownDisplay.innerText = `You have ${countdown} seconds to focus on the target text field...`;
        } else {
          clearInterval(countdownInterval);
          countdownDisplay.innerText = '';
          // Start typing simulation
          startTypingSimulation(text, wpm, pauses, includePauses);
        }
      }, 1000);
    });
  
    const closeButton = document.getElementById('closeButton');
    closeButton.addEventListener('click', function() {
      uiContainer.remove();
    });
  
    // Function to calculate estimated time
    function calculateEstimatedTime(text, wpm, pauses, includePauses) {
      const words = text.trim().split(/\s+/).length;
      const timePerWord = 60 / wpm;
      let totalTypingTime = words * timePerWord;
  
      let totalPauseTime = 0;
      if (includePauses) {
        const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0).length;
        const paragraphs = text.split(/\n\n+/).filter(p => p.trim().length > 0).length;
        const midSentencePauses = words; // Approximate mid-sentence pauses
  
        totalPauseTime += sentences * (pauses.pauseSentence || 0);
        totalPauseTime += paragraphs * (pauses.pauseParagraph || 0);
        totalPauseTime += midSentencePauses * ((pauses.pauseMin + pauses.pauseMax) / 2);
      }
  
      return totalTypingTime + totalPauseTime;
    }
  
    // Function to start typing simulation
    async function startTypingSimulation(text, wpm, pauses, includePauses) {
      // Disable the start button to prevent multiple clicks
      startButton.disabled = true;
      startButton.innerText = 'Typing...';
  
      // Calculate typing speed
      const typingSpeed = 60000 / (wpm * 5); // Approximate time per character
  
      // Focus on the current active element
      const targetElement = document.activeElement;
      if (!targetElement) {
        alert('Please focus on a text field where you want to simulate typing.');
        startButton.disabled = false;
        startButton.innerText = 'Start Typing';
        return;
      }
  
      // Start debugging
      chrome.runtime.sendMessage({ action: 'startDebugging' }, async (response) => {
        if (response && response.success) {
          // Proceed with typing
          await performTypingSimulation(text, typingSpeed, pauses, includePauses);
        } else {
          alert('Failed to start debugging.');
          startButton.disabled = false;
          startButton.innerText = 'Start Typing';
        }
      });
    }
  
    // Function to perform the actual typing simulation
    async function performTypingSimulation(text, typingSpeed, pauses, includePauses) {
      // Parse formatted text
      const formattedText = parseFormattedText(text);
  
      // Simulate typing
      for (let segment of formattedText) {
        const content = segment.text;
  
        for (let i = 0; i < content.length; i++) {
          const char = content[i];
  
          await typeCharacter(char, typingSpeed);
  
          // Check for pauses
          if (includePauses) {
            if (char === '.' || char === '!' || char === '?') {
              // Pause after sentence
              if (pauses.pauseSentence > 0) {
                await sleep(pauses.pauseSentence * 1000);
              }
            } else if (char === '\n' && content[i + 1] === '\n') {
              // Pause after paragraph (detect double line breaks)
              if (pauses.pauseParagraph > 0) {
                await sleep(pauses.pauseParagraph * 1000);
              }
            } else if (char === ' ') {
              // Pause mid-sentence (randomized between pauseMin and pauseMax)
              if (pauses.pauseMidSentence > 0) {
                const pauseTime = pauses.pauseMin + Math.random() * (pauses.pauseMax - pauses.pauseMin);
                await sleep(pauseTime * 1000);
              }
            }
          }
        }
      }
  
      // Stop debugging
      chrome.runtime.sendMessage({ action: 'stopDebugging' });
  
      // Re-enable the start button
      startButton.disabled = false;
      startButton.innerText = 'Start Typing';
      alert('Typing simulation completed.');
    }
  
    // Function to type a character using the debugger API
    async function typeCharacter(char, typingSpeed) {
      let keyEvent = {};
  
      if (char === '\n') {
        // Handle newline character
        keyEvent = {
          type: 'keyDown',
          key: 'Enter',
          code: 'Enter',
          keyCode: 13,
          windowsVirtualKeyCode: 13,
          nativeVirtualKeyCode: 13,
        };
      } else if (char === ' ') {
        // Handle space character
        keyEvent = {
          type: 'keyDown',
          key: ' ',
          code: 'Space',
          keyCode: 32,
          windowsVirtualKeyCode: 32,
          text: ' ',
        };
      } else {
        // Handle regular character
        keyEvent = {
          type: 'keyDown',
          key: char,
          text: char,
        };
      }
  
      // Send keyDown
      chrome.runtime.sendMessage({ action: 'dispatchKeyEvent', event: keyEvent });
  
      // Modify event for keyUp
      keyEvent.type = 'keyUp';
  
      // Send keyUp
      chrome.runtime.sendMessage({ action: 'dispatchKeyEvent', event: keyEvent });
  
      await sleep(typingSpeed);
    }
  
    function sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    }
  
    // Function to parse formatted text
    function parseFormattedText(text) {
      // Currently, formatting may not be supported with debugger API
      // Returning the entire text without formatting
      return [{ text: text, bold: false, italic: false }];
    }
  })();
  