document.addEventListener("DOMContentLoaded", () => {
  // Seletores dos elementos
  const browseBtn = document.getElementById("browse-btn");
  const fileInput = document.getElementById("file-input");
  const dropArea = document.getElementById("drop-area");
  const uploadPrompt = document.getElementById("upload-prompt");
  const fileConfirmation = document.getElementById("file-confirmation");
  const fileNameDisplay = document.getElementById("file-name");
  const removeFileBtn = document.getElementById("remove-file-btn");
  const emailTextarea = document.getElementById("email-textarea");
  const analyzeBtn = document.getElementById("analyze-btn");

  const resultsOutput = document.getElementById("results-output");
  // Salva o HTML do placeholder para podermos restaurá-lo
  const resultsPlaceholder =
    document.getElementById("results-output").innerHTML;

  // Endereço do Backend
  const API_BASE_URL = "";

  // Botão "Procurar arquivo"
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
    emailTextarea.value = "";
    resultsOutput.innerHTML = resultsPlaceholder; // Restaura o placeholder
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
        emailTextarea.value = e.target.result;
        console.log("Arquivo .txt carregado no textarea.");
      };
      reader.readAsText(file);
    } else if (file.type === "application/pdf") {
      reader.onload = (e) => {
        const base64content = e.target.result.split(",")[1];
        console.log("PDF lido como Base64. Enviando para o backend...");
        processPdfInBackend(base64content, file.name);
      };
      reader.readAsDataURL(file);
    } else {
      alert("Tipo de arquivo não suportado. Por favor, use .txt ou .pdf.");
      removeFileBtn.click();
    }
  });

  // Processar PDF no Backend
  async function processPdfInBackend(base64, filename) {
    emailTextarea.value = "Extraindo texto do PDF, aguarde... 🤖";
    try {
      const response = await fetch(`${API_BASE_URL}/extract-text-from-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content_base64: base64,
          filename: filename,
        }),
      });
      if (!response.ok)
        throw new Error(`Erro do servidor: ${response.statusText}`);
      const data = await response.json();
      emailTextarea.value = data.text_content;
      console.log("Texto do PDF extraído com sucesso!");
    } catch (error) {
      console.error("Falha ao processar PDF no backend:", error);
      alert("Não foi possível extrair o texto do PDF. Verifique o backend.");
      emailTextarea.value = `Falha ao ler o arquivo PDF "${filename}".`;
    }
  }

  // Botão "Iniciar Análise"
  analyzeBtn.addEventListener("click", async () => {
    const textContent = emailTextarea.value;

    if (
      !textContent ||
      textContent.trim() === "" ||
      textContent.startsWith("Extraindo texto")
    ) {
      alert("Por favor, cole um texto ou aguarde o carregamento do arquivo.");
      return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.querySelector("span").textContent = "Analisando...";
    resultsOutput.innerHTML = `
        <div class="flex flex-col items-center gap-3 text-center">
            <span class="material-symbols-outlined text-[var(--text-muted)] text-9xl animate-spin">sync</span>
            <p class="text-[var(--text-dark)] text-2xl font-semibold">Analisando...</p>
            <p class="text-[var(--text-muted)] text-base font-normal">
                Aguarde, a IA está classificando seu e-mail.
            </p>
        </div>`;

    // Verifica se a tela de confirmação está visível
    const isFile = !fileConfirmation.classList.contains("hidden");

    // Cria o objeto JSON
    const jsonObject = {
      filename: isFile ? fileNameDisplay.textContent : "textarea_input",
      fileType: isFile ? "application/pdf_or_txt" : "text/plain",
      content: textContent,
    };

    console.log("JSON para análise:", jsonObject);
    // Chama a API do backend
    try {
      const response = await fetch(`${API_BASE_URL}/classify-email`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(jsonObject),
      });

      if (!response.ok) {
        throw new Error(
          `Erro na API: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();
      // Exibe os resultados
      const categoryClass =
        data.category.toLowerCase() === "produtivo"
          ? "bg-blue-100 text-blue-800"
          : "bg-green-100 text-green-800";

      resultsOutput.innerHTML = `
          <div class="flex flex-col gap-6 text w-full">
              <div>
                  <h4 class="text-sm font-semibold text-[var(--text-muted)] uppercase">Categoria</h4>
                  <span class="inline-block px-3 py-1 mt-2 text-lg font-bold rounded-full ${categoryClass}">
                      ${data.category}
                  </span>
              </div>
              <div>
                  <h4 class="text-sm font-semibold text-[var(--text-muted)] uppercase">Resposta Sugerida</h4>
                  <pre class="mt-2 p-4 rounded-lg bg-white border border-[var(--border-light)] whitespace-pre-wrap font-sans text-base text-[var(--text-dark)]">${data.suggested_reply}</pre>
              </div>
          </div>`;
    } catch (error) {
      // Exibe mensagem de erro
      console.error("Falha ao classificar:", error);
      resultsOutput.innerHTML = `
          <div class="flex flex-col items-center gap-3 text-center">
              <span class="material-symbols-outlined text-red-500 text-9xl">error</span>
              <p class="text-[var(--text-dark)] text-2xl font-semibold">Erro na Análise</p>
              <p class="text-[var(--text-muted)] text-base font-normal">
                  Não foi possível conectar à API. Verifique o console e o backend.
              </p>
          </div>`;
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.querySelector("span").textContent = "Iniciar Análise";
    }
  });
});
