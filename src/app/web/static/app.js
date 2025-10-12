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
    setStatus('❌ Ditado por voz não suportado neste navegador. Use Chrome, Edge ou Safari.', true);
    return;
  }

  // Verificar se está em HTTPS (necessário para Web Speech API)
  if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
    setStatus('❌ Ditado por voz requer HTTPS. Acesse via https:// ou localhost.', true);
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
      errorMessage = '🎤 Permissão de microfone negada!\n\n' +
                    '📋 Como permitir:\n' +
                    '1. Clique no ícone 🔒 ou 🎤 na barra de endereços\n' +
                    '2. Selecione "Permitir" para microfone\n' +
                    '3. Recarregue a página (F5)\n' +
                    '4. Tente o ditado novamente\n\n' +
                    '💡 Dica: Em alguns navegadores, você precisa interagir com a página primeiro (clique em qualquer lugar).';
    } else if (event.error === 'no-speech') {
      errorMessage = '🔇 Nenhuma fala detectada.\n\n' +
                    '💡 Dicas:\n' +
                    '• Fale mais próximo ao microfone\n' +
                    '• Verifique se o microfone não está mudo\n' +
                    '• Tente falar mais alto e claro';
    } else if (event.error === 'audio-capture') {
      errorMessage = '🎤 Erro na captura de áudio.\n\n' +
                    '🔧 Verificações:\n' +
                    '• Microfone está conectado?\n' +
                    '• Outros aplicativos estão usando o microfone?\n' +
                    '• Tente fechar outros programas de áudio';
    } else if (event.error === 'network') {
      errorMessage = '🌐 Erro de rede durante o ditado.\n\n' +
                    '📡 Soluções:\n' +
                    '• Verifique sua conexão com a internet\n' +
                    '• Tente novamente em alguns segundos\n' +
                    '• Use o modo offline se disponível';
    } else if (event.error === 'service-not-allowed') {
      errorMessage = '🚫 Serviço de reconhecimento de voz não permitido.\n\n' +
                    '⚙️ Verificações:\n' +
                    '• Configurações de privacidade do navegador\n' +
                    '• Extensões que bloqueiam microfone\n' +
                    '• Modo incógnito pode ter restrições';
    } else if (event.error === 'bad-grammar') {
      errorMessage = '📝 Erro na gramática do reconhecimento de voz.\n\n' +
                    '🔄 Tente novamente com fala mais clara.';
    } else if (event.error === 'language-not-supported') {
      errorMessage = '🌍 Idioma português não suportado para ditado neste navegador.\n\n' +
                    '🔄 Tente usar Chrome ou Edge mais recentes.';
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
    setStatus('🎤 Ditando... Fale agora!');
  } catch (error) {
    console.error('Erro ao iniciar ditado:', error);
    setStatus('❌ Erro ao iniciar ditado. Verifique as permissões do microfone e tente novamente.', true);
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

// Adicionar funcionalidade de envio com Enter
if (messageInput) {
  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Previne quebra de linha
      
      // Verificar se há conteúdo para enviar
      const content = messageInput.value.trim();
      if (content) {
        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        form.submit();
      }
    }
    // Shift+Enter permite quebra de linha (comportamento padrão)
  });
}

window.addEventListener('beforeunload', () => {
  if (recording) {
    stopRecording();
  }
  stopDictation();
});

// Theme toggle and recommendations
(function initEnhancements() {
  const themeToggle = document.getElementById('theme-toggle');
  const recoButton = document.getElementById('reco-button');
  const recoQuery = document.getElementById('reco-query');
  const recoResults = document.getElementById('reco-results');

  if (themeToggle) {
    const saved = localStorage.getItem('sparkone-theme');
    if (saved === 'light') document.body.setAttribute('data-theme', 'light');
    themeToggle.addEventListener('click', () => {
      const isLight = document.body.getAttribute('data-theme') === 'light';
      if (isLight) {
        document.body.removeAttribute('data-theme');
        localStorage.removeItem('sparkone-theme');
      } else {
        document.body.setAttribute('data-theme', 'light');
        localStorage.setItem('sparkone-theme', 'light');
      }
    });
  }

  const renderPlaces = (payload) => {
    if (!recoResults) return;
    recoResults.innerHTML = '';
    if (!payload || !payload.items || !payload.items.length) {
      const msg = document.createElement('div');
      msg.className = 'status';
      msg.textContent = payload && payload.message ? payload.message : 'Nenhum resultado encontrado.';
      recoResults.appendChild(msg);
      return;
    }
    for (const p of payload.items) {
      const item = document.createElement('div');
      item.className = 'list-item';
      item.innerHTML = `<div><strong>${p.name || 'Local'}</strong><br/><small>${p.address || ''}</small></div><div><small>${p.rating ? '⭐ ' + p.rating : ''}</small></div>`;
      recoResults.appendChild(item);
    }
  };

  const fetchPlaces = async (query, coords) => {
    const params = new URLSearchParams({ q: query || '' });
    if (coords) {
      params.set('lat', coords.latitude);
      params.set('lng', coords.longitude);
    }
    const res = await fetch(`/recommendations/places?${params.toString()}`);
    renderPlaces(await res.json());
  };

  if (recoButton && recoQuery) {
    recoButton.addEventListener('click', async () => {
      setStatus('Buscando recomendações...');
      const q = recoQuery.value || 'cafés';
      const coords = await new Promise((resolve) => {
        if (!navigator.geolocation) return resolve(null);
        navigator.geolocation.getCurrentPosition((pos) => resolve(pos.coords), () => resolve(null), { enableHighAccuracy: true, timeout: 4000 });
      });
      try {
        await fetchPlaces(q, coords);
      } catch (e) {
        console.error(e);
        renderPlaces({ items: [], message: 'Erro ao buscar recomendações.' });
      } finally {
        resetStatus();
      }
    });
  }
})();
