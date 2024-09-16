document.addEventListener('DOMContentLoaded', function() {
    // Open the first tab by default
    openTab('TextInput');
  
    // Attach event listeners to tab buttons
    const tabLinks = document.querySelectorAll('.tablink');
    tabLinks.forEach(function(tabLink) {
      tabLink.addEventListener('click', function(event) {
        const tabName = this.getAttribute('data-tab');
        openTab(tabName);
      });
    });
  
    // Update WPM value display
    const wpmRange = document.getElementById('wpmRange');
    const wpmValue = document.getElementById('wpmValue');
    wpmRange.addEventListener('input', function() {
      wpmValue.innerText = this.value;
    });
  
    // Toggle pauses settings
    const includePausesCheckbox = document.getElementById('includePauses');
    const pausesSettingsDiv = document.getElementById('pausesSettings');
    includePausesCheckbox.addEventListener('change', function() {
      pausesSettingsDiv.style.display = this.checked ? 'block' : 'none';
    });
  
    // Start typing when the button is clicked
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
          pauseSentence: parseFloat(document.getElementById('pauseSentence').value) || 0,
          pauseParagraph: parseFloat(document.getElementById('pauseParagraph').value) || 0,
          pauseMidSentence: parseFloat(document.getElementById('pauseMidSentence').value) || 0,
          pauseMin: parseFloat(document.getElementById('pauseMin').value) || 0,
          pauseMax: parseFloat(document.getElementById('pauseMax').value) || 0
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
          // Send message to content script
          chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
            const activeTab = tabs[0];
            chrome.scripting.executeScript({
              target: { tabId: activeTab.id },
              files: ['content.js']
            }, function() {
              chrome.tabs.sendMessage(activeTab.id, {
                action: 'startTyping',
                text: text,
                wpm: wpm,
                pauses: pauses,
                includePauses: includePauses
              });
              window.close(); // Close the popup after starting
            });
          });
        }
      }, 1000);
    });
  });
  
  // Function to open tabs
  function openTab(tabName) {
    const tabContents = document.getElementsByClassName('tabcontent');
    for (let i = 0; i < tabContents.length; i++) {
      tabContents[i].style.display = 'none';
    }
  
    const tabLinks = document.getElementsByClassName('tablink');
    for (let i = 0; i < tabLinks.length; i++) {
      tabLinks[i].style.backgroundColor = '';
    }
  
    const activeTab = document.getElementById(tabName);
    if (activeTab) {
      activeTab.style.display = 'block';
    }
  
    const activeButton = document.querySelector('.tablink[data-tab="' + tabName + '"]');
    if (activeButton) {
      activeButton.style.backgroundColor = '#ccc';
    }
  }
  
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
  