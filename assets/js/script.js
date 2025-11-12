document.addEventListener("DOMContentLoaded", () => {
  // --- 1. SELETORES ---
  const browseBtn = document.getElementById("browse-btn");
  const fileInput = document.getElementById("file-input");
  const dropArea = document.getElementById("drop-area");
  const uploadPrompt = document.getElementById("upload-prompt");
  const fileConfirmation = document.getElementById("file-confirmation");
  const fileNameDisplay = document.getElementById("file-name");
  const removeFileBtn = document.getElementById("remove-file-btn");

  // Seletores para o Textarea e o botão de Análise
  const emailTextarea = document.getElementById("email-textarea");
  const analyzeBtn = document.getElementById("analyze-btn");

  // Botão "Procurar Arquivo"
  browseBtn.addEventListener("click", () => {
    fileInput.click();
  });

  // Drag and drop
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropArea.addEventListener(
      eventName,
      (event) => {
        event.preventDefault();
        event.stopPropagation();
      },
      false
    );
  });
  ["dragenter", "dragover"].forEach((eventName) => {
    dropArea.addEventListener(
      eventName,
      () => {
        dropArea.classList.add("border-[var(--accent-blue)]");
      },
      false
    );
  });
  ["dragleave", "drop"].forEach((eventName) => {
    dropArea.addEventListener(
      eventName,
      () => {
        dropArea.classList.remove("border-[var(--accent-blue)]");
      },
      false
    );
  });
  dropArea.addEventListener(
    "drop",
    (event) => {
      const files = event.dataTransfer.files;
      if (files.length > 0) {
        fileInput.files = files;
        const changeEvent = new Event("change", { bubbles: true });
        fileInput.dispatchEvent(changeEvent);
      }
    },
    false
  );

  // Remover arquivo selecionado
  removeFileBtn.addEventListener("click", () => {
    fileInput.value = null;
    fileConfirmation.classList.add("hidden");
    uploadPrompt.classList.remove("hidden");

    // Limpa o textarea também
    emailTextarea.value = "";
  });

  // Leitura do arquivo selecionado
  fileInput.addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (!file) return;

    fileNameDisplay.textContent = file.name;
    uploadPrompt.classList.add("hidden");
    fileConfirmation.classList.remove("hidden");

    console.log("Processando arquivo...", file.name);
    const reader = new FileReader();

    if (file.type === "text/plain") {
      reader.onload = (e) => {
        const textContent = e.target.result;

        // Preenche o textarea com o conteúdo do .txt
        emailTextarea.value = textContent;

        console.log("Arquivo .txt carregado no textarea.");
      };
      reader.readAsText(file);
    } else if (file.type === "application/pdf") {
      console.log("Leitura de PDF não implementada");
    } else {
      console.error("Erro: Tipo de arquivo não suportado.");
      alert("Tipo de arquivo não suportado. Por favor, use .txt ou .pdf.");
      removeFileBtn.click();
    }
  });

  //  BOTÃO "INICIAR ANÁLISE"
  analyzeBtn.addEventListener("click", () => {
    const textContent = emailTextarea.value;

    // Verifica se o textarea não está vazio
    if (!textContent || textContent.trim() === "") {
      alert(
        "Por favor, cole um texto ou carregue um arquivo .txt para analisar."
      );
      return;
    }

    // Cria o objeto JSON com o conteúdo do textarea
    const jsonObject = {
      filename: "textarea_input",
      fileType: "text/plain",
      content: textContent,
    };

    // Mostra o JSON no console
    console.log("JSON do Textarea:", jsonObject);
  });
});
