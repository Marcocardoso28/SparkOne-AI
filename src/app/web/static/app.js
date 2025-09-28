const form = document.getElementById('message-form');
const recordButton = document.getElementById('record-button');
const speechButton = document.getElementById('speech-button');
const imageInput = document.getElementById('image-input');
const audioInput = document.getElementById('audio-file');
const imagePreview = document.getElementById('image-preview');
const audioPreview = document.getElementById('audio-preview');
const statusEl = document.getElementById('status');
const messageInput = document.getElementById('message-input');

let mediaRecorder = null;
let audioChunks = [];
let recognition = null;
let recording = false;
let dictating = false;

const resetStatus = () => {
  if (statusEl) {
    statusEl.textContent = '';
  }
};

const setStatus = (message, isError = false) => {
  if (!statusEl) return;
  statusEl.textContent = message;
  statusEl.style.color = isError ? '#fca5a5' : 'rgba(226,232,240,0.75)';
};

const updateRecordButton = () => {
  if (!recordButton) return;
  recordButton.textContent = recording ? '⏹️ Parar gravação' : '🎙️ Gravar áudio';
  recordButton.classList.toggle('button--recording', recording);
};

const clearAudioPreview = () => {
  if (!audioPreview) return;
  audioPreview.hidden = true;
  const audioTag = audioPreview.querySelector('audio');
  if (audioTag && audioTag.src) {
    URL.revokeObjectURL(audioTag.src);
  }
  if (audioTag) {
    audioTag.src = '';
  }
  audioChunks = [];
  if (audioInput) {
    audioInput.value = '';
  }
};

const clearImagePreview = () => {
  if (!imagePreview) return;
  imagePreview.hidden = true;
  const img = imagePreview.querySelector('img');
  if (img && img.src) {
    URL.revokeObjectURL(img.src);
  }
  if (img) {
    img.src = '';
  }
  if (imageInput) {
    imageInput.value = '';
  }
};

const startRecording = async () => {
  if (!navigator.mediaDevices?.getUserMedia) {
    setStatus('Gravação não suportada neste navegador.', true);
    return;
  }
  clearAudioPreview();
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };
    mediaRecorder.onstop = () => {
      const blob = new Blob(audioChunks, { type: 'audio/webm' });
      if (blob.size === 0) {
        clearAudioPreview();
        setStatus('Nenhum áudio capturado.', true);
        return;
      }
      const url = URL.createObjectURL(blob);
      if (audioPreview) {
        const audioTag = audioPreview.querySelector('audio');
        if (audioTag) {
          audioTag.src = url;
        }
        audioPreview.hidden = false;
      }
      if (audioInput) {
        const file = new File([blob], `sparkone-audio-${Date.now()}.webm`, { type: 'audio/webm' });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        audioInput.files = dataTransfer.files;
      }
      setStatus('Gravação pronta para envio.');
    };
    mediaRecorder.start();
    recording = true;
    updateRecordButton();
    setStatus('Gravando...');
  } catch (error) {
    console.error('Erro ao acessar microfone:', error);
    let errorMessage = 'Não foi possível acessar o microfone.';
    
    if (error.name === 'NotAllowedError') {
      errorMessage = 'Permissão de microfone negada. Clique no ícone de microfone na barra de endereços e permita o acesso.';
    } else if (error.name === 'NotFoundError') {
      errorMessage = 'Nenhum microfone encontrado. Verifique se há um microfone conectado.';
    } else if (error.name === 'NotReadableError') {
      errorMessage = 'Microfone está sendo usado por outro aplicativo. Feche outros programas que possam estar usando o microfone.';
    } else if (error.name === 'OverconstrainedError') {
      errorMessage = 'Configurações de áudio não suportadas pelo dispositivo.';
    } else if (error.name === 'SecurityError') {
      errorMessage = 'Acesso ao microfone bloqueado por política de segurança. Verifique se está usando HTTPS.';
    }
    
    setStatus(errorMessage, true);
  }
};

const stopRecording = () => {
  if (mediaRecorder && recording) {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach((track) => track.stop());
  }
  recording = false;
  updateRecordButton();
};

if (recordButton) {
  recordButton.addEventListener('click', async () => {
    resetStatus();
    if (!recording) {
      await startRecording();
    } else {
      stopRecording();
    }
  });
}

const startDictation = () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    setStatus('Ditado por voz não suportado neste navegador.', true);
    return;
  }
  recognition = new SpeechRecognition();
  recognition.lang = 'pt-BR';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    if (messageInput) {
      if (messageInput.value && !messageInput.value.endsWith(' ')) {
        messageInput.value += ' ';
      }
      messageInput.value += transcript;
      messageInput.focus();
    }
  };
  recognition.onerror = (event) => {
    console.error('Erro no ditado:', event.error);
    let errorMessage = `Erro no ditado: ${event.error}`;
    
    if (event.error === 'not-allowed') {
      errorMessage = 'Permissão de microfone negada para ditado. Clique no ícone de microfone na barra de endereços e permita o acesso.';
    } else if (event.error === 'no-speech') {
      errorMessage = 'Nenhuma fala detectada. Tente falar mais próximo ao microfone.';
    } else if (event.error === 'audio-capture') {
      errorMessage = 'Erro na captura de áudio. Verifique se o microfone está funcionando.';
    } else if (event.error === 'network') {
      errorMessage = 'Erro de rede durante o ditado. Verifique sua conexão com a internet.';
    } else if (event.error === 'service-not-allowed') {
      errorMessage = 'Serviço de reconhecimento de voz não permitido. Verifique as configurações do navegador.';
    } else if (event.error === 'bad-grammar') {
      errorMessage = 'Erro na gramática do reconhecimento de voz.';
    } else if (event.error === 'language-not-supported') {
      errorMessage = 'Idioma português não suportado para ditado neste navegador.';
    }
    
    setStatus(errorMessage, true);
  };
  recognition.onend = () => {
    dictating = false;
    if (speechButton) {
      speechButton.textContent = '🗣️ Ditado';
    }
  };
  
  try {
    recognition.start();
    dictating = true;
    if (speechButton) {
      speechButton.textContent = '🛑 Parar ditado';
    }
    setStatus('Ditando... Fale agora.');
  } catch (error) {
    console.error('Erro ao iniciar ditado:', error);
    setStatus('Erro ao iniciar ditado. Tente novamente.', true);
  }
};

const stopDictation = () => {
  if (recognition && dictating) {
    recognition.stop();
  }
  dictating = false;
  if (speechButton) {
    speechButton.textContent = '🗣️ Ditado';
  }
};

if (speechButton) {
  speechButton.addEventListener('click', () => {
    resetStatus();
    if (!dictating) {
      startDictation();
    } else {
      stopDictation();
    }
  });
}

if (imageInput && imagePreview) {
  imageInput.addEventListener('change', () => {
    resetStatus();
    const img = imagePreview.querySelector('img');
    if (img && img.src) {
      URL.revokeObjectURL(img.src);
    }
    const [file] = imageInput.files || [];
    if (!file) {
      clearImagePreview();
      return;
    }
    const url = URL.createObjectURL(file);
    if (img) {
      img.src = url;
    }
    imagePreview.hidden = false;
  });
}

if (imagePreview) {
  const removeBtn = imagePreview.querySelector('[data-target="image"]');
  if (removeBtn) {
    removeBtn.addEventListener('click', () => {
      clearImagePreview();
    });
  }
}

if (audioPreview) {
  const removeBtn = audioPreview.querySelector('[data-target="audio"]');
  if (removeBtn) {
    removeBtn.addEventListener('click', () => {
      stopRecording();
      clearAudioPreview();
      setStatus('Áudio removido.');
    });
  }
}

if (form) {
  form.addEventListener('submit', () => {
    resetStatus();
    stopDictation();
    if (recording) {
      stopRecording();
    }
    setStatus('Enviando mensagem...');
    
    // Limpar pré-visualizações
    clearImagePreview();
    clearAudioPreview();
  });
}

window.addEventListener('beforeunload', () => {
  if (recording) {
    stopRecording();
  }
  stopDictation();
});
