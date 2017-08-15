let btn = document.createElement('button');
btn.innerText = 'Download as PDF';
btn.setAttribute("id", "downloadButton")
btn.onclick = function(){window.print();};
document.body.appendChild(btn);

// Check when the onload function fires
window.onload = function () { console.log('loaded'); 
                              console.log(document.getElementById('pie')); // If this fires an error then the react page hasn't finished loading
                            }
