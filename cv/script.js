window.onload = function () {
  console.log("adding");
  const fadeInElements = document.querySelectorAll(".splash");
  fadeInElements.forEach((el) => {
    el.classList.add("loaded");
  });
};

function formSubmit(event) {
  try {
    event.preventDefault(); // Prevent the form from submitting normally
    let emailAlert = document.getElementById("alert-email-success");

    emailjs.init({ publicKey: "8dpzcRv3NFnbdN1s9" });

    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const message = document.getElementById("message").value;

    const templateParams = {
      name: name,
      email: email,
      message: message,
    };

    emailjs.send("service_jng7e0g", "template_ojqkpod", templateParams).then(
      function (response) {
        console.log("Success!", response.status, response.text);
        emailAlert.hidden = false;
      },
      function (error) {
        console.error("Failed...", error);
      }
    );

    return false;
  } catch (err) {
    console.error(err);
  }
}
