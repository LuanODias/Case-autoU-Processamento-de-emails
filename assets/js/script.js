document.addEventListener("DOMContentLoaded", () => {
  const browseBtn = document.getElementById("browse-btn");
  const fileInput = document.getElementById("file-input");

  // Abre o gerenciador de arquivos ao clicar no botão
  browseBtn.addEventListener("click", () => {
    fileInput.click();
  });

  // Lê o arquivo e converte para JSON ao ser selecionado
  fileInput.addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (!file) {
      return; // O usuário cancelou
    }

    // Mensagem de processamento no console
    console.log("Processando arquivo...", file.name);

    // Cria um filereader para ler o arquivo
    const reader = new FileReader();

    // Caso 1: Arquivo .TXT
    if (file.type === "text/plain") {
      // Diz ao reader para executar esta função quando terminar
      reader.onload = (e) => {
        const textContent = e.target.result;

        // Criação do objeto JSON
        const jsonObject = {
          filename: file.name,
          fileType: file.type,
          content: textContent,
        };

        // Mostra o objeto JSON no console
        console.log("JSON do .txt:", jsonObject);
      };

      // Inicia a leitura do arquivo como Texto
      reader.readAsText(file);

      // --- Caso 2: Arquivo .PDF ---
    } else if (file.type === "application/pdf") {
      // Diz ao leitor para executar esta função quando terminar
      reader.onload = (e) => {
        const dataUrl = e.target.result; // Data URL (Base64)
        const base64content = dataUrl.split(",")[1];

        // Criamos o objeto JSON.
        const jsonObject = {
          filename: file.name,
          fileType: file.type,
          content_base64: base64content, // Enviando o conteúdo completo
        };

        // Mostra o objeto JSON no console
        console.log("JSON do .pdf (Base64):", jsonObject);
      };

      // Inicia a leitura do arquivo como Data URL (Base64)
      reader.readAsDataURL(file);
    } else {
      // Mostra o erro no console
      console.error("Erro: Tipo de arquivo não suportado.");
    }

    // Limpa o valor do input para permitir reenvio do mesmo arquivo se necessário
    fileInput.value = null;
  });
});
