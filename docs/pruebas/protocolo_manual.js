// Ejecución real del protocolo manual de la versión 3.0 (navegador Chromium, servidor local).
const {chromium}=require('playwright');const fs=require('fs');
// Uso: SGR_URL=http://127.0.0.1:8000 SGR_CLAVE_DEMO=<clave de las cuentas demo> node docs/pruebas/protocolo_manual.js
// Requiere un ambiente de pruebas con datos de demostración (reiniciar_demo + cargar_datos_iniciales).
const path=require('path');
const URL=process.env.SGR_URL||'http://127.0.0.1:8000', EV=path.join(__dirname,'evidencias')+'/', CLAVE=process.env.SGR_CLAVE_DEMO;
const RAIZ=path.join(__dirname,'..','..')+'/';
if(!CLAVE){console.error('Falta SGR_CLAVE_DEMO');process.exit(1);}
// Claves de prueba generadas en cada ejecución (no se guardan en el repositorio).
const azar=()=>require('crypto').randomBytes(6).toString('hex');
const CLAVE_NUEVA='Sgr.'+azar()+'.Nv', CLAVE_RECUPERADA='Sgr.'+azar()+'.Rc';
const R=[];
(async()=>{
const b=await chromium.launch();
b.newContext=(o=>{const f=b.constructor.prototype.newContext;return async function(x){const c=await f.call(b,x);c.setDefaultTimeout(8000);return c;}})();
async function nueva(){const c=await b.newContext({viewport:{width:1280,height:860}});return [c,await c.newPage()];}
async function entrar(p,u,clave){await p.goto(URL+'/cuentas/ingresar/');await p.fill('input[name=usuario]',u);await p.fill('input[name=contrasena]',clave||CLAVE);
  await Promise.all([p.waitForLoadState('load'),p.click('button[type=submit]')]);await p.waitForTimeout(300);}
async function caso(id,fn){const ini=new Date();let estado='Aprobado',obt='';
  try{obt=await fn();}catch(e){estado='Reprobado';obt=String(e).slice(0,300);}
  R.push({id,estado,obtenido:obt,fecha:ini.toISOString()});console.log(id,estado,obt);}
const local=(ms)=>new Date(ms).toLocaleDateString('en-CA',{timeZone:'America/Santiago'});const hoy=local(Date.now());

await caso('CP-MAN-01',async()=>{const out=[];for(const [u,txt] of [['funcionario.rural','Mi panel'],['delegado.rural','Mi delegación'],['coordinador.sgr','Delegaciones'],['verificador.sgr','Auditoría'],['admin.sgr','Mantenedores']]){
  const [c,p]=await nueva();await entrar(p,u);const ok=(await p.textContent('nav')).includes(txt);if(!ok)throw new Error(u+' sin menú '+txt);out.push(u);if(u==='delegado.rural')await p.screenshot({path:EV+'MAN-01_panel_delegado.png'});await c.close();}
  return 'Cada rol entra a su panel con su menú: '+out.join(', ');});

let nuevoUsuario='',claveTemp='';
await caso('CP-MAN-02',async()=>{const [c,p]=await nueva();await entrar(p,'delegado.rural');
  await p.goto(URL+'/organizacion/funcionarios/nuevo/');
  await p.fill('#id_nombre','Paula Rivas Prueba');await p.fill('#id_rut','16.000.000-7');await p.fill('#id_email','p.rivas.prueba@laserena.cl');
  const cargo=await p.$('#id_cargo');if(cargo){const ops=await p.$$eval('#id_cargo option',o=>o.map(x=>x.value).filter(Boolean));await p.selectOption('#id_cargo',ops[0]);}
  await Promise.all([p.waitForLoadState('load'),p.click('form:not([action$="/salir/"]) button[type=submit]')]);await p.waitForTimeout(300);
  const msg=await p.textContent('body');const m=msg.match(/usuario «([^»]+)», contraseña temporal «([^»]+)»/);
  if(!m)throw new Error('No se mostró la contraseña temporal');nuevoUsuario=m[1];claveTemp=m[2];
await c.close();
  const [c2,p2]=await nueva();await entrar(p2,nuevoUsuario,claveTemp);await p2.goto(URL+'/gestion/');
  if(!p2.url().includes('/cuentas/cambiar-clave/'))throw new Error('No obligó a cambiar la clave: '+p2.url());
  await p2.screenshot({path:EV+'MAN-02_cambio_obligatorio.png'});
  await p2.fill('#id_old_password',claveTemp);await p2.fill('#id_new_password1',CLAVE_NUEVA);await p2.fill('#id_new_password2',CLAVE_NUEVA);
  await Promise.all([p2.waitForLoadState('load'),p2.click('form:not([action$="/salir/"]) button[type=submit]')]);await p2.goto(URL+'/gestion/');
  if(p2.url().includes('cambiar-clave'))throw new Error('Sigue pidiendo cambio');await c2.close();
  return `El Delegado creó la cuenta ${nuevoUsuario}; al ingresar con la clave temporal se exigió cambiarla y después accedió normalmente.`;});

await caso('CP-MAN-03',async()=>{const dir=RAIZ+'logs/correos/';const antes=fs.existsSync(dir)?fs.readdirSync(dir).length:0;
  const [c,p]=await nueva();await p.goto(URL+'/cuentas/ingresar/');await p.click('text=¿Olvidó su contraseña?');
  await p.fill('#id_email','p.rivas.prueba@laserena.cl');await Promise.all([p.waitForLoadState('load'),p.click('form:not([action$="/salir/"]) button[type=submit]')]);
  await p.screenshot({path:EV+'MAN-03_revise_correo.png'});
  const archivos=fs.readdirSync(dir).sort((a,b)=>fs.statSync(dir+a).mtimeMs-fs.statSync(dir+b).mtimeMs);if(archivos.length<=antes)throw new Error('No se generó correo');
  const cuerpo=fs.readFileSync(dir+archivos[archivos.length-1],'utf8').replace(/=\r?\n/g,'');const enlace=cuerpo.match(/http:\/\/[^\s]+\/cuentas\/restablecer\/[^\s]+\//)[0];
  await p.goto(enlace.replace('http://testserver',URL));await p.waitForTimeout(300);
  await p.fill('#id_new_password1',CLAVE_RECUPERADA);await p.fill('#id_new_password2',CLAVE_RECUPERADA);
  await Promise.all([p.waitForLoadState('load'),p.click('form:not([action$="/salir/"]) button[type=submit]')]);
  await p.screenshot({path:EV+'MAN-03_restablecida.png'});
  await p.goto(enlace.replace('http://testserver',URL));const usado=(await p.textContent('body')).includes('Enlace no válido');
  await c.close();const [c2,p2]=await nueva();await entrar(p2,nuevoUsuario,CLAVE_RECUPERADA);const ok=!p2.url().includes('ingresar');await c2.close();
  if(!usado||!ok)throw new Error('enlace reutilizable o login fallido');
  return 'Llegó el correo con el enlace; se creó una clave nueva, el enlace quedó inválido al reutilizarlo y se ingresó con la clave nueva.';});

let codigoAct='';
await caso('CP-MAN-04',async()=>{const [c,p]=await nueva();await entrar(p,'funcionario.rural');await p.goto(URL+'/gestion/nueva/');
  const cat=await p.$$eval('#id_categoria option',o=>o.map(x=>x.value).filter(Boolean));await p.selectOption('#id_categoria',cat[0]);
  await p.fill('#id_fecha',hoy);await p.fill('#id_descripcion','Visita a vecina por luminaria (protocolo)');
  await p.fill('#id_contacto','Rosa Pérez');await p.fill('#id_telefono_contacto','+56 9 1234 5678');
  await p.setInputFiles('#id_evidencia',RAIZ+'static/img/escudo-la-serena.jpg');
  await Promise.all([p.waitForLoadState('load'),p.click('form:not([action$="/salir/"]) button[type=submit]')]);await p.waitForTimeout(300);
  const t=await p.textContent('body');const m=t.match(/código ([A-Z]{2}-\d{4})/);if(!m||!t.includes('Suma puntaje'))throw new Error('sin código o no suma');codigoAct=m[1];
  await p.screenshot({path:EV+'MAN-04_actividad_registrada.png'});await c.close();return `Actividad ${codigoAct} registrada con evidencia; la ficha muestra "Suma puntaje" y estado Pendiente.`;});

await caso('CP-MAN-05',async()=>{const [c,p]=await nueva();await entrar(p,'delegado.rural');await p.goto(URL+'/gestion/?q='+codigoAct);
  await p.click(`text=${codigoAct}`).catch(()=>{});await p.goto(URL+'/gestion/?q='+codigoAct);const href=await p.getAttribute('a.deleg-card-link','href');await p.goto(URL+href);
  await p.check('input[value=antecedentes]');await p.fill('#id_observacion','Falta la lista de asistencia');
  await Promise.all([p.waitForLoadState('load'),p.click('button[name=revisar]')]);
  if(!(await p.textContent('body')).includes('Faltan antecedentes'))throw new Error('no quedó en antecedentes');await p.screenshot({path:EV+'MAN-05_mas_antecedentes.png'});await c.close();
  const [c2,p2]=await nueva();await entrar(p2,'funcionario.rural');await p2.goto(URL+href);
  await p2.setInputFiles('input[name=archivo]',RAIZ+'static/img/escudo-la-serena.jpg');
  await Promise.all([p2.waitForLoadState('load'),p2.click('button[name=subir_evidencia]')]);
  const pend=(await p2.textContent('body')).includes('Pendiente de validación');await c2.close();if(!pend)throw new Error('no volvió a pendiente');
  const [c3,p3]=await nueva();await entrar(p3,'delegado.rural');await p3.goto(URL+href);await p3.check('input[value=aprobar]');
  await Promise.all([p3.waitForLoadState('load'),p3.click('button[name=revisar]')]);const ok=(await p3.textContent('body')).includes('Validada');
  await p3.screenshot({path:EV+'MAN-05_aprobada.png'});await c3.close();if(!ok)throw new Error('no se aprobó');
  globalThis.HREF=href;return 'El Delegado pidió antecedentes; el funcionario subió otra evidencia y volvió a Pendiente; el Delegado la aprobó.';});

await caso('CP-MAN-06',async()=>{const [c,p]=await nueva();await entrar(p,'funcionario.rural');const r=await p.goto(URL+globalThis.HREF+'editar/');
  const st=r.status();await p.screenshot({path:EV+'MAN-06_aprobada_bloqueada.png'});await c.close();const [c2,p2]=await nueva();await entrar(p2,'admin.sgr');const r2=await p2.goto(URL+globalThis.HREF+'editar/');const st2=r2.status();await c2.close();
  if(st!==403||st2!==403)throw new Error('status '+st+' '+st2);return 'Modificar una actividad aprobada responde 403 para el Funcionario y para el Administrador.';});

await caso('CP-MAN-07',async()=>{const [c,p]=await nueva();await entrar(p,'funcionario.rural');await p.goto(URL+'/gestion/gestion-social/nueva/');
  const cat=await p.$$eval('#id_categoria option',o=>o.map(x=>x.value).filter(Boolean));await p.selectOption('#id_categoria',cat[0]);
  const st=await p.$$eval('#id_subtipo_atencion option',o=>o.map(x=>x.value).filter(Boolean));await p.selectOption('#id_subtipo_atencion',st[0]);
  await p.fill('#id_fecha',hoy);await p.fill('#id_descripcion','Postulación a PGU (protocolo)');
  const caja=await p.$('input[aria-label="Buscar vecino por RUT o nombre"]');await caja.type('Rosa',{delay:40});await p.waitForTimeout(800);
  await p.screenshot({path:EV+'MAN-07_autocompletar.png'});await p.click('.autocompletar-lista button');
  const sel=await p.inputValue('#id_vecino');if(!sel)throw new Error('autocompletar no eligió vecino');
  await p.check('#id_ingresar_al_tubo');await Promise.all([p.waitForLoadState('load'),p.click('form:not([action$="/salir/"]) button[type=submit]')]);await p.waitForTimeout(300);
  if(!p.url().includes('/gestion/agenda/nuevo/'))throw new Error('no fue al Tubo: '+p.url());const rut=await p.inputValue('#id_rut_solicitante');
  if(!(await p.inputValue('#id_territorio')))throw new Error('el territorio no se completó desde el vecino');
  await p.fill('#id_fecha_compromiso',local(Date.now()+5*864e5));
  await Promise.all([p.waitForLoadState('load'),p.click('form:not([action$="/salir/"]) button[type=submit]')]);await p.screenshot({path:EV+'MAN-07_ingreso_al_tubo.png'});
  const creado=(await p.textContent('body')).includes('agregado a la agenda colectiva');await c.close();if(!creado)throw new Error('el compromiso no se creó');
  if(!rut)throw new Error('sin RUT del solicitante');globalThis.RUT=rut;return `Gestión social registrada con el vecino elegido por autocompletar; ingresó al Tubo con RUT ${rut}.`;});

await caso('CP-MAN-08',async()=>{const [c,p]=await nueva();await entrar(p,'delegado.rural');await p.goto(URL+'/gestion/agenda/');
  const total=Number(await p.textContent('#total-tubo'));await p.fill('[data-busqueda-dinamica="#tabla-tubo"]',globalThis.RUT.slice(0,6));await p.waitForTimeout(400);
  const vis=Number(await p.textContent('#total-tubo'));await p.screenshot({path:EV+'MAN-08_busqueda_dinamica.png'});await c.close();
  if(!(vis>=1&&vis<total))throw new Error(`visibles ${vis} de ${total}`);return `Al escribir parte del RUT la lista se filtró sin recargar: ${vis} de ${total} compromisos.`;});

await caso('CP-MAN-09',async()=>{const [c,p]=await nueva();await entrar(p,nuevoUsuario,CLAVE_RECUPERADA);await p.goto(URL+'/gestion/cartas/nueva/');
  await p.fill('#id_fecha_ingreso',hoy);await p.fill('#id_para','Delegado');await p.fill('#id_remite','Club Adulto Mayor (protocolo)');await p.fill('#id_tema','Solicita uso de sede');
  await Promise.all([p.waitForLoadState('load'),p.click('form:not([action$="/salir/"]) button[type=submit]')]);await c.close();
  const [c2,p2]=await nueva();await entrar(p2,'funcionario.rural');await p2.goto(URL+'/gestion/cartas/');const fila=await p2.$('tr:has-text("Club Adulto Mayor (protocolo)")');
  const txt=await fila.textContent();await p2.screenshot({path:EV+'MAN-09_tubo_cartas.png'});await c2.close();if(!txt.includes('Solo lectura'))throw new Error('otro funcionario puede modificar');
  return 'La carta de otra funcionaria aparece en el Tubo de cartas del funcionario, en solo lectura.';});

await caso('CP-MAN-10',async()=>{const [c,p]=await nueva();await entrar(p,'funcionario.rural');await p.goto(URL+'/gestion/nueva/');
  const cat=await p.$$eval('#id_categoria option',o=>o.map(x=>x.value).filter(Boolean));await p.selectOption('#id_categoria',cat[0]);
  await p.fill('#id_fecha',local(Date.now()-12*864e5));await p.fill('#id_descripcion','Actividad atrasada');
  await Promise.all([p.waitForLoadState('load'),p.click('form:not([action$="/salir/"]) button[type=submit]')]);const t=await p.textContent('body');await p.screenshot({path:EV+'MAN-10_semana_cerrada.png'});await c.close();
  if(!t.includes('semana ya está cerrada'))throw new Error('aceptó una semana cerrada');return 'Una actividad de hace 12 días se rechazó con el mensaje de semana cerrada.';});

await caso('CP-MAN-11',async()=>{const [c,p]=await nueva();await entrar(p,'delegado.rural');await p.goto(URL+'/gestion/dashboard/');await p.waitForTimeout(800);
  const n=await p.$$eval('canvas',x=>x.length);const ops=await p.$$eval('select[name=funcionario] option',o=>o.map(x=>x.value).filter(Boolean));
  await p.selectOption('select[name=funcionario]',ops[0]);await Promise.all([p.waitForLoadState('load'),p.click('text=Aplicar')]);await p.waitForTimeout(800);
  const filas=await p.$$eval('table.dash-tabla tbody tr',x=>x.length);await p.screenshot({path:EV+'MAN-11_dashboard_filtrado.png',fullPage:true});await c.close();
  if(n<4||filas!==1)throw new Error(`graficos ${n}, filas ${filas}`);return `El dashboard muestra ${n} gráficos; al filtrar por un funcionario queda solo su fila.`;});

await caso('CP-MAN-12',async()=>{const [c,p]=await nueva();await entrar(p,'funcionario.rural');const r=await p.goto(URL+'/auditoria/');const st=r.status();await c.close();
  const [c2,p2]=await nueva();await entrar(p2,'verificador.sgr');await p2.goto(URL+'/auditoria/');const fila=(await p2.textContent('tbody')).includes('Acceso denegado');
  await p2.screenshot({path:EV+'MAN-12_acceso_denegado_auditado.png'});await c2.close();if(st!==403||!fila)throw new Error('status '+st);
  return 'El Funcionario recibió 403 en /auditoria/ y el Verificador ve el intento como "Acceso denegado".';});

fs.writeFileSync(path.join(__dirname,'resultados_manuales.json'),JSON.stringify(R,null,1));await b.close();})();
