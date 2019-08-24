var inputs = ["formMRU", "formCRU", "formSRU", "formHRU"];
inputs.forEach(function(id) {
    var slider = document.getElementById(id);
    var output = document.getElementById(id+"Value");
    output.innerHTML = slider.value; // Display the default slider value

    // Update the current slider value (each time you drag the slider handle)
    slider.oninput = function() {
        output.innerHTML = this.value;
    }
});