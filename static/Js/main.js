// Interacciones conservadas y adaptadas a rutas de Django.
// Calendario: mostrar de a tres meses, como en la versión original de El Poli.
let paginaActual = 0;
const mesesPorPagina = 3;

function mostrarMeses() {
    const meses = document.querySelectorAll('.calendario-anual .mes-cajita');
    if (!meses.length) return;

    const totalPaginas = Math.ceil(meses.length / mesesPorPagina);
    paginaActual = Math.max(0, Math.min(paginaActual, totalPaginas - 1));
    const inicio = paginaActual * mesesPorPagina;
    const fin = inicio + mesesPorPagina;

    meses.forEach((mes, indice) => {
        mes.hidden = indice < inicio || indice >= fin;
    });

    const anterior = document.getElementById('mesesAnterior');
    const siguiente = document.getElementById('mesesSiguiente');
    if (anterior) anterior.disabled = paginaActual === 0;
    if (siguiente) siguiente.disabled = paginaActual === totalPaginas - 1;
}

function cambiarMeses(direccion) {
    paginaActual += direccion;
    mostrarMeses();
}

function cambiarModo() {
    document.body.classList.toggle('dark-mode');
    const activo = document.body.classList.contains('dark-mode');
    localStorage.setItem('modoOscuro', activo ? 'activado' : 'desactivado');
    actualizarBotonTema();
}
function actualizarBotonTema() {
    const boton = document.getElementById('btnTema');
    if (!boton) return;
    const activo = document.body.classList.contains('dark-mode');
    const icono = boton.querySelector('.theme-icon');
    const texto = boton.querySelector('.theme-label');
    if (icono) icono.textContent = activo ? '☀' : '◐';
    if (texto) texto.textContent = activo ? 'Claro' : 'Tema';
    boton.title = activo ? 'Usar tema claro' : 'Usar tema oscuro';
}
function buscarEnTabla() {
    const input = document.getElementById('inputBuscador');
    if (!input) return;
    const consulta = input.value.trim().toLowerCase();
    document.querySelectorAll('#cuerpoTabla tr:not(.fila-vacia)').forEach((fila) => {
        fila.style.display = fila.innerText.toLowerCase().includes(consulta) ? '' : 'none';
    });
}
function buscarConEnter(event) {
    if (event.key === 'Enter') { event.preventDefault(); buscarEnTabla(); }
}
function abrirModal(fecha = '') {
    const modal = document.getElementById('miModal');
    const inputFecha = document.getElementById('inputFecha');
    const estado = document.getElementById('nuevo_estado');
    if (inputFecha) inputFecha.value = fecha;
    if (estado) estado.value = fecha ? 'reservado' : '';
    if (modal) modal.style.display = 'flex';
}
function cerrarModal() {
    const modal = document.getElementById('miModal');
    if (modal) modal.style.display = 'none';
}
function configurarCierreModales() {
    document.querySelectorAll('.modal-overlay').forEach((modal) => {
        modal.addEventListener('mousedown', (event) => {
            if (event.target === modal) modal.style.display = 'none';
        });
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') cerrarModal();
    });
}
function configurarScrollPersistente() {
    document.querySelectorAll('#miModal form, .formulario-ancho').forEach((formulario) => {
        formulario.addEventListener('submit', () => {
            sessionStorage.setItem('scrollPos', String(window.scrollY));
        });
    });
    const pos = sessionStorage.getItem('scrollPos');
    if (pos !== null) {
        window.scrollTo(0, Number.parseInt(pos, 10) || 0);
        sessionStorage.removeItem('scrollPos');
    }
}
document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('modoOscuro') === 'activado') document.body.classList.add('dark-mode');
    actualizarBotonTema();
    mostrarMeses();
    configurarCierreModales();
    configurarScrollPersistente();
});
