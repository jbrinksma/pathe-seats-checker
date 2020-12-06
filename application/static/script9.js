const searchMovies = document.forms['search-movies'].querySelector('input');
const searchCinemas = document.forms['search-cinemas'].querySelector('input');

searchMovies.addEventListener('keyup', function(e){
    const term = e.target.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const movies = document.getElementsByClassName("movie_container");
    Array.from(movies).forEach(function(movie){
        const title = movie.getAttribute("name");
        if (title.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").indexOf(term) != -1){
            movie.style.display = 'block';
        } else {
            movie.style.display = "none";
        }
    });
});

searchCinemas.addEventListener('keyup', function(e){
    const term = e.target.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const cinemas = document.getElementsByClassName("cinema_container");
    const movies = document.getElementsByClassName("movie_container");
    Array.from(cinemas).forEach(function(cinema){
        const title = cinema.getAttribute("name");
        if (title.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").indexOf(term) != -1){
            cinema.style.display = 'block';
        } else {
            cinema.style.display = "none";
        }
    });
    // Hide empty movie_container's as a result of this search
    Array.from(movies).forEach(function(movie){
        var movie_cinemas = movie.children;
        console.log(movie);
        var visible_childs = false;
        Array.from(movie_cinemas).forEach(function(child) {
            if (child.getAttribute("class") == "cinema_container" && child.style.display != "none") {
                visible_childs = true;
            }
        });
        console.log(visible_childs);
        if (!visible_childs) {
            console.log("rekt");
            movie.style.display = "none";
        } else {
            console.log("rektnot");
            movie.style.display = "block";
        }
    });
});