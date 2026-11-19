function reveal(image){
  if(!(image instanceof HTMLImageElement)||!image.hasAttribute('data-pending-image')||!image.complete||!image.naturalWidth)return;
  image.hidden=false;
  image.style.removeProperty('display');
  image.removeAttribute('data-pending-image');
}
document.addEventListener('load',event=>reveal(event.target),true);
for(const image of document.querySelectorAll('img[data-pending-image]'))reveal(image);
