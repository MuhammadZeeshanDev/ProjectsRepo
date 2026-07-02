/*const container = document.querySelector('.container');
const songListUl = document.querySelector('.songlist ul');
const playBtn = document.getElementById('play');
const prevBtn = document.getElementById('previous');
const nextBtn = document.getElementById('next');
const songInfo = document.querySelector('.song-info');
const durationDiv = document.querySelector('.duration');
const seekbar = document.querySelector('.seekbar');
const circle = document.querySelector('.seekbar .circle');


let albums = [];
let currentAlbum = null;
let currentSongIndex = 0;
let audio = new Audio();
let isPlaying = false;

// Fetch all album JSON files in 'generated/'
fetch('generated/albums.json')
    .then(res => res.json())
    .then(data => {
        albums = data;
        displayAlbumCards();
    })
    .catch(err => console.error(err));

// Display album cards
function displayAlbumCards() {
    container.innerHTML = '';
    albums.forEach(album => {
        const card = document.createElement('div');
        card.classList.add('cardcontainer');


        const img = document.createElement('img');
        img.src = `Songs/${album.album}/${album.cover}`;
        img.alt = album.title;
        img.classList.add('img1');

        const info = document.createElement('div');
        info.textContent = album.title;
        info.classList.add('card-info');

        card.appendChild(img);
        card.appendChild(info);

        card.addEventListener('click', () => {
            currentAlbum = album;
            currentSongIndex = 0;
            displayPlaylist(album);
            loadSong();
        });

        container.appendChild(card);
    });
}

// Display playlist
function displayPlaylist(album) {
    songListUl.innerHTML = '';
    album.songs.forEach((song, index) => {
        const li = document.createElement('li');
        li.textContent = `${song.title} - ${song.artist}`;
        li.addEventListener('click', () => {
            currentSongIndex = index;
            loadSong();
            playSong();

        });
        songListUl.appendChild(li);
    });
}

// Load current song
function loadSong() {
    if (!currentAlbum) return;
    const song = currentAlbum.songs[currentSongIndex];
    const url = `${song.filename}`;
    audio.src = decodeURIComponent(url);
    songInfo.textContent = `${song.title} - ${song.artist}`;
    console.log(audio.src)

    audio.addEventListener('loadedmetadata', () => updateDuration());
    audio.addEventListener('timeupdate', () => {
        updateSeekbar();
        updateCurrentTime();
    });
    audio.addEventListener('ended', nextSong);
}

// Play/Pause
function playSong() {
    if (!currentAlbum) return;
    audio.play();
    isPlaying = true;
    playBtn.src = 'Images/pause.svg';
}

function pauseSong() {
    audio.pause();
    isPlaying = false;
    playBtn.src = 'Images/play.svg';
}

playBtn.addEventListener('click', () => {
    if (!currentAlbum) return;
    isPlaying ? pauseSong() : playSong();
});

// Next / Previous
nextBtn.addEventListener('click', nextSong);
prevBtn.addEventListener('click', () => {
    if (!currentAlbum) return;
    currentSongIndex = (currentSongIndex - 1 + currentAlbum.songs.length) % currentAlbum.songs.length;
    loadSong();
    playSong();
});

function nextSong() {
    if (!currentAlbum) return;
    currentSongIndex = (currentSongIndex + 1) % currentAlbum.songs.length;
    loadSong();
    playSong();
}

// Seekbar
seekbar.addEventListener('click', e => {
    if (!currentAlbum || !audio.duration) return;
    const rect = seekbar.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    audio.currentTime = percent * audio.duration;
});

function updateSeekbar() {
    if (!audio.duration) return;
    const percent = (audio.currentTime / audio.duration) * 100;
    circle.style.left = `${percent}%`;
}

function updateDuration() {
    if (!audio.duration) return;
    durationDiv.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration)}`;
    durationDiv.classList.add("duration");
}

function updateCurrentTime() {
    if (!audio.duration) return;
    durationDiv.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration)}`;
    durationDiv.classList.add("duration");
}

function formatTime(sec) {
    const minutes = Math.floor(sec / 60) || 0;
    const seconds = Math.floor(sec % 60) || 0;
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

document.querySelector(".hamburger").addEventListener("click", () => {
        document.querySelector(".left").style.left = "0%";

});

document.querySelector(".close").addEventListener("click", () => {
        document.querySelector(".left").style.left = "-100vw";
});*/

// DOM Elements
const container = document.querySelector('.container');
const songListUl = document.querySelector('.songlist ul');
const playBtn = document.getElementById('play');
const prevBtn = document.getElementById('previous');
const nextBtn = document.getElementById('next');
const songInfo = document.querySelector('.song-info');
const durationDiv = document.querySelector('.duration');
const seekbar = document.querySelector('.seekbar');
const circle = document.querySelector('.seekbar .circle');

let albums = [];
let currentAlbum = null;
let currentSongNode = null; // now using linked list
let audio = new Audio();
let isPlaying = false;

// ------------------ Linked List Node ------------------
class SongNode {
    constructor(song) {
        this.song = song;
        this.next = null;
        this.prev = null;
    }
}

// Create a doubly linked list from album songs
function createLinkedList(songs) {
    let head = null;
    let prevNode = null;

    songs.forEach(song => {
        const node = new SongNode(song);
        if (!head) head = node;

        if (prevNode) {
            prevNode.next = node;
            node.prev = prevNode;
        }
        prevNode = node;
    });

    // Make it circular
    prevNode.next = head;
    head.prev = prevNode;

    return head;
}

// ------------------ Fetch Albums ------------------
fetch('generated/albums.json')
    .then(res => res.json())
    .then(data => {
        albums = data;
        displayAlbumCards();
    })
    .catch(err => console.error(err));

// ------------------ Display Albums ------------------
function displayAlbumCards() {
    container.innerHTML = '';
    albums.forEach(album => {
        const card = document.createElement('div');
        card.classList.add('cardcontainer');

        const img = document.createElement('img');
        img.src = `Songs/${album.album}/${album.cover}`;
        img.alt = album.title;
        img.classList.add('img1');

        const info = document.createElement('div');
        info.textContent = album.title;
        info.classList.add('card-info');

        card.appendChild(img);
        card.appendChild(info);

        card.addEventListener('click', () => {
            currentAlbum = album;
            currentSongNode = createLinkedList(album.songs); // linked list head
            displayPlaylist(album);
            loadSongNode(currentSongNode);
        });

        container.appendChild(card);
    });
}

// ------------------ Display Playlist ------------------
function displayPlaylist(album) {
    songListUl.innerHTML = '';
    album.songs.forEach((song, index) => {
        const li = document.createElement('li');
        li.textContent = `${song.title} - ${song.artist}`;
        li.addEventListener('click', () => {
            // Find the node corresponding to clicked song
            let node = currentSongNode;
            while (node.song.filename !== song.filename) node = node.next;
            currentSongNode = node;
            loadSongNode(currentSongNode);
            playSong();
        });
        songListUl.appendChild(li);
    });
}

// ------------------ Load Song Node ------------------
function loadSongNode(node) {
    if (!node) return;
    audio.src = decodeURIComponent(node.song.filename);
    songInfo.textContent = `${node.song.title} - ${node.song.artist}`;

    audio.addEventListener('loadedmetadata', () => updateDuration());
    audio.addEventListener('timeupdate', () => {
        updateSeekbar();
        updateCurrentTime();
    });
    audio.addEventListener('ended', nextSong);
}

// ------------------ Play / Pause ------------------
function playSong() {
    if (!currentSongNode) return;
    audio.play();
    isPlaying = true;
    playBtn.src = 'Images/pause.svg';
}

function pauseSong() {
    audio.pause();
    isPlaying = false;
    playBtn.src = 'Images/play.svg';
}

playBtn.addEventListener('click', () => {
    if (!currentSongNode) return;
    isPlaying ? pauseSong() : playSong();
});

// ------------------ Next / Previous ------------------
nextBtn.addEventListener('click', nextSong);
prevBtn.addEventListener('click', prevSong);

function nextSong() {
    if (!currentSongNode) return;
    currentSongNode = currentSongNode.next;
    loadSongNode(currentSongNode);
    playSong();
}

function prevSong() {
    if (!currentSongNode) return;
    currentSongNode = currentSongNode.prev;
    loadSongNode(currentSongNode);
    playSong();
}

// ------------------ Seekbar ------------------
seekbar.addEventListener('click', e => {
    if (!currentSongNode || !audio.duration) return;
    const rect = seekbar.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    audio.currentTime = percent * audio.duration;
});

function updateSeekbar() {
    if (!audio.duration) return;
    const percent = (audio.currentTime / audio.duration) * 100;
    circle.style.left = `${percent}%`;
}

function updateDuration() {
    if (!audio.duration) return;
    durationDiv.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration)}`;
}

function updateCurrentTime() {
    if (!audio.duration) return;
    durationDiv.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration)}`;
}

function formatTime(sec) {
    const minutes = Math.floor(sec / 60) || 0;
    const seconds = Math.floor(sec % 60) || 0;
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

// ------------------ Hamburger Menu ------------------
document.querySelector(".hamburger").addEventListener("click", () => {
    document.querySelector(".left").style.left = "0%";
});

document.querySelector(".close").addEventListener("click", () => {
    document.querySelector(".left").style.left = "-100vw";
});
