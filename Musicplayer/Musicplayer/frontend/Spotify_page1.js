document.querySelector(".start-button").addEventListener("click", () => {
    console.log("Clicked")
    document.querySelector(".button-online").style.animation = "after-start-button1 0.5s ease 0s forwards";
    document.querySelector(".button-offline").style.animation = "after-start-button2 0.5s ease 0s forwards";
    document.querySelector(".start-button").style.opacity = "0"
    document.querySelector(".section-right").style.filter = "blur(4px)"
    document.querySelector(".section-left").style.filter = "blur(4px)"
    document.querySelector(".section-mid").style.filter = "blur(100px)"
})         