// JavaScript Document

$(document).ready(function() {
	// Testinomial Carousel Start
	$('.testinomial-carousel').slick({
		dots: true,
		arrows: false,
		infinite: false,
		adaptiveHeight: true,
		speed: 300,
		fade: true,
		slidesToShow: 1,
		slidesToScroll: 1,
	});
	// Testinomial Carousel End

	// AOS Start
	AOS.init();
	// AOS End

	// OFI Browser
	objectFitImages();
});
