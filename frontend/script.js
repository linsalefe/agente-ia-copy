document.getElementById("emailForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const product = document.getElementById("product").value;
    const objective = document.getElementById("objective").value;
    const briefing = document.getElementById("briefing").value;

    const payload = {
        product: product,
        objective: objective,
        briefing: briefing
    };

    document.getElementById("response").innerHTML = "Gerando e-mail... ⏳";

    try {
        const res = await fetch("http://127.0.0.1:8000/email/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (data.error) {
            document.getElementById("response").innerHTML = "❌ Erro: " + data.error;
            return;
        }

        document.getElementById("response").innerHTML = `
            <h3>Email Gerado</h3>
            <strong>Assunto:</strong><br>${data.assunto}<br><br>
            <strong>Corpo:</strong><br>${data.corpo.replace(/\n/g, "<br>")}
        `;

    } catch (error) {
        console.error(error);
        document.getElementById("response").innerHTML = "❌ Erro ao conectar com o servidor.";
    }
});
