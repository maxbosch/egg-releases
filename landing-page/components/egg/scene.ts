import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EGG_COUNT, EGG_COLORS, clamp, smooth, seed, meadowPosition, terrainHeight, scrollPhases } from './game';

type Callbacks = { onCollect: (id: number) => void; onError: () => void };

// Both shell pieces share an irregular rim. At zero separation they form one egg.
export function eggGeometry(half?: 'top' | 'bottom') {
  const columns = 64, rows = 32;
  const positions: number[] = [], indices: number[] = [];
  for (let j = 0; j <= rows; j++) for (let i = 0; i <= columns; i++) {
    const angle = i / columns * Math.PI * 2;
    const teeth = Math.asin(Math.sin(angle * 9)) / (Math.PI / 2);
    const seam = Math.acos(teeth * .105 + Math.sin(angle * 3) * .025);
    const v = j / rows;
    const phi = half === 'top' ? v * seam : half === 'bottom' ? seam + v * (Math.PI - seam) : v * Math.PI;
    const y = Math.cos(phi), radius = Math.sin(phi) * (1 - .19 * y);
    positions.push(Math.cos(angle) * radius, y * 1.32, Math.sin(angle) * radius);
    if (j < rows && i < columns) {
      const a = j * (columns + 1) + i, b = a + columns + 1;
      indices.push(a, a + 1, b, b, a + 1, b + 1);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.setIndex(indices); geo.computeVertexNormals();
  return geo;
}

export function createEggScene(mount: HTMLDivElement, meadowElement: HTMLElement, callbacks: Callbacks) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.7));
  renderer.setClearColor(0xc5d9f4, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.25;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  mount.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog('#c5d9f4', 30, 90);
  const camera = new THREE.PerspectiveCamera(35, 1, .1, 150);
  const environment = new RoomEnvironment();
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envTarget = pmrem.fromScene(environment, .08);
  scene.environment = envTarget.texture;
  environment.dispose(); pmrem.dispose();
  scene.add(new THREE.HemisphereLight('#ecfbff', '#739534', 2.5));
  const sun = new THREE.DirectionalLight('#fff1cf', 4.2);
  sun.position.set(-7, 13, 8); sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024); sun.shadow.camera.left = -12; sun.shadow.camera.right = 12;
  sun.shadow.camera.top = 12; sun.shadow.camera.bottom = -12; sun.shadow.normalBias = .05;
  scene.add(sun);
  const fill = new THREE.DirectionalLight('#bedfff', 1.5); fill.position.set(5, 3, -5); scene.add(fill);
  const giant = new THREE.Group(); scene.add(giant);
  const shellMaterial = new THREE.MeshPhysicalMaterial({color:'#fffaeb', roughness:.22, metalness:.02, clearcoat:.65, clearcoatRoughness:.16, side:THREE.DoubleSide});
  const shellTop = new THREE.Mesh(eggGeometry('top'), shellMaterial);
  const shellBottom = new THREE.Mesh(eggGeometry('bottom'), shellMaterial);
  giant.add(shellTop, shellBottom); giant.scale.setScalar(1.15);
  const miniGeometry = eggGeometry();
  const materials = EGG_COLORS.map(color => new THREE.MeshPhysicalMaterial({color, roughness:.2, metalness:.08, clearcoat:1, clearcoatRoughness:.12}));
  const eggs = Array.from({length:EGG_COUNT}, (_, id) => {
    const mesh = new THREE.Mesh(miniGeometry, materials[id % materials.length]);
    mesh.castShadow = true; mesh.receiveShadow = true; mesh.userData.id = id;
    scene.add(mesh);
    return {id, mesh, destination:new THREE.Vector3(...meadowPosition(id)), collected:false, collectedAt:0, start:new THREE.Vector3(), order:0};
  });

  const landscape = new THREE.Group(); landscape.visible = false; scene.add(landscape);
  const groundGeo = new THREE.PlaneGeometry(100, 100, 100, 100);
  groundGeo.rotateX(-Math.PI/2);
  const groundPos = groundGeo.attributes.position;
  for(let i=0;i<groundPos.count;i++) groundPos.setY(i, terrainHeight(groundPos.getX(i),groundPos.getZ(i)));
  groundGeo.computeVertexNormals();
  const ground = new THREE.Mesh(groundGeo,new THREE.MeshStandardMaterial({color:'#78aa45',roughness:1}));
  ground.receiveShadow=true; landscape.add(ground);
  // Instancing keeps a dense field of grass inexpensive on phones.
  const bladeGeo = new THREE.BufferGeometry();
  bladeGeo.setAttribute('position',new THREE.Float32BufferAttribute([-.03,0,0,.03,0,0,.022,.24,0,-.016,.24,0,.09,.48,0],3));
  bladeGeo.setIndex([0,1,2,0,2,3,3,2,4]); bladeGeo.computeVertexNormals();
  const grassMaterial = new THREE.MeshStandardMaterial({color:'#87b945',roughness:1,side:THREE.DoubleSide});
  grassMaterial.onBeforeCompile = shader => {
    shader.uniforms.uTime = {value:0};
    grassMaterial.userData.shader = shader;
    shader.vertexShader = 'uniform float uTime;\n' + shader.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\ntransformed.x += sin(uTime * 1.3 + instanceMatrix[3].x * .8 + instanceMatrix[3].z) * .1 * pow(position.y / .48, 2.0);');
  };
  const grassCount = window.innerWidth < 700 ? 6000 : 13000;
  const grass = new THREE.InstancedMesh(bladeGeo,grassMaterial,grassCount);
  const dummy = new THREE.Object3D(), color = new THREE.Color();
  for(let i=0;i<grassCount;i++) {
    const x=(seed(i+100)-.5)*35, z=(seed(i+17000)-.5)*28;
    dummy.position.set(x,terrainHeight(x,z)-.01,z);
    dummy.rotation.set(0,seed(i+35000)*Math.PI*2,0);
    dummy.scale.setScalar(.45+seed(i+6000)*.8); dummy.updateMatrix(); grass.setMatrixAt(i,dummy.matrix);
    color.setHSL(.20+seed(i+901)*.08,.45,.30+seed(i+734)*.13);grass.setColorAt(i,color);
  }
  grass.frustumCulled=false; landscape.add(grass);
  // Small flowers and rounded distant hills make the play area feel like a meadow.
  const flowerGeo = new THREE.SphereGeometry(.055,6,4);
  const flowers = new THREE.InstancedMesh(flowerGeo,new THREE.MeshStandardMaterial({roughness:.7}),220);
  for(let i=0;i<220;i++) {
    const x=(seed(i+467)-.5)*23,z=(seed(i+782)-.5)*19;
    dummy.position.set(x,terrainHeight(x,z)+.3,z);dummy.rotation.set(0,0,0);dummy.scale.set(1.2,.5,1.2);dummy.updateMatrix();flowers.setMatrixAt(i,dummy.matrix);
    flowers.setColorAt(i,new THREE.Color(i%3===0?'#fff5d5':i%3===1?'#f2c548':'#c6b2ee'));
  }
  landscape.add(flowers);
  const hillGeo = new THREE.SphereGeometry(1,32,16);
  const hillMaterials = ['#769d50','#91ad5e','#a4ba70'].map(c=>new THREE.MeshStandardMaterial({color:c,roughness:1}));
  for(let i=0;i<9;i++) {
    const hill=new THREE.Mesh(hillGeo,hillMaterials[i%3]);hill.position.set((i-4)*9,-2,-19-seed(i)*12);hill.scale.set(8+seed(i+1)*5,4+seed(i+2)*3,8);landscape.add(hill);
  }
  const basket = new THREE.Group(); basket.position.set(0,terrainHeight(0,4.4),4.4);landscape.add(basket);
  const basketMat = new THREE.MeshStandardMaterial({color:'#ba7840',roughness:.65});
  const basketDarkMat = new THREE.MeshStandardMaterial({color:'#7d4927',roughness:1});
  const base = new THREE.Mesh(new THREE.CylinderGeometry(.78,.6,.12,40),basketDarkMat);base.position.y=.08;base.receiveShadow=true;basket.add(base);
  const ringGeo = new THREE.TorusGeometry(1,.035,5,48);
  for(let j=0;j<8;j++) {
    const ring=new THREE.Mesh(ringGeo,basketMat);ring.rotation.x=Math.PI/2;ring.position.y=.12+j*.083;
    ring.scale.setScalar(.64+j*.03);ring.castShadow=true;basket.add(ring);
  }
  const strutGeo = new THREE.CylinderGeometry(.022,.022,.69,5);
  for(let i=0;i<26;i++) {
    const a=i/26*Math.PI*2;
    const strut=new THREE.Mesh(strutGeo,basketMat);strut.position.set(Math.cos(a)*.75,.36,Math.sin(a)*.75);
    strut.rotation.z=-Math.cos(a)*.29;strut.rotation.x=Math.sin(a)*.29;basket.add(strut);
  }
  const handle = new THREE.Mesh(new THREE.TorusGeometry(.85,.046,7,40,Math.PI),basketMat);handle.position.y=.6;basket.add(handle);

  const pointer = new THREE.Vector2(0,0), raycaster=new THREE.Raycaster();
  const startTime=performance.now(); let disposed=false, frame=0, hovered=-1, lastCount=0;
  let width=1,height=1, meadowTop=0, lastScroll=-1, lastMeadow=-1, lastFrame=0, lastRenderedCount=-1;
  const media=window.matchMedia('(prefers-reduced-motion: reduce)');
  let reduced=media.matches;
  const onReduced=()=>{reduced=media.matches;};media.addEventListener('change',onReduced);
  function measure(){width=window.innerWidth;height=window.innerHeight;camera.aspect=width/height;camera.updateProjectionMatrix();renderer.setSize(width,height);meadowTop=meadowElement.getBoundingClientRect().top+window.scrollY;}
  const observer = new ResizeObserver(measure);observer.observe(document.body);window.addEventListener('resize',measure);measure();
  function currentPhases(){return scrollPhases(window.scrollY,height,meadowTop);}
  function collect(id:number){
    const egg=eggs[id];if(!egg||egg.collected)return;
    egg.collected=true;egg.collectedAt=performance.now();egg.start.copy(egg.mesh.position);egg.order=lastCount++;
    callbacks.onCollect(id);
  }
  function reset(){lastCount=0;for(const egg of eggs){egg.collected=false;egg.collectedAt=0;egg.mesh.visible=true;}}
  const projected=new THREE.Vector3();
  function hit(clientX:number,clientY:number){
    if(currentPhases().meadow<.95)return -1;
    pointer.set(clientX/width*2-1,-clientY/height*2+1);raycaster.setFromCamera(pointer,camera);
    const hits=raycaster.intersectObjects(eggs.filter(e=>!e.collected).map(e=>e.mesh));
    if(hits.length)return hits[0].object.userData.id as number;
    // Generous touch target around small eggs, without overlapping collection state.
    let nearest=-1, distance=28;
    eggs.forEach(egg=>{if(egg.collected)return;projected.copy(egg.mesh.position).project(camera);
      const d=Math.hypot((projected.x+1)*width/2-clientX,(1-projected.y)*height/2-clientY);
      if(projected.z<1&&d<distance){distance=d;nearest=egg.id;}
    });return nearest;
  }
  function move(event:PointerEvent){hovered=hit(event.clientX,event.clientY);mount.style.cursor=hovered>=0?'pointer':'default';}
  let downX=0,downY=0;
  function down(e:PointerEvent){downX=e.clientX;downY=e.clientY;}
  function up(e:PointerEvent){if(Math.hypot(e.clientX-downX,e.clientY-downY)>10)return;const id=hit(e.clientX,e.clientY);if(id>=0)collect(id);}
  renderer.domElement.addEventListener('pointermove',move);renderer.domElement.addEventListener('pointerdown',down);renderer.domElement.addEventListener('pointerup',up);
  const contextLost=(event:Event)=>{event.preventDefault();callbacks.onError();};renderer.domElement.addEventListener('webglcontextlost',contextLost);
  const target=new THREE.Vector3(), position=new THREE.Vector3();
  const initialCamera = new THREE.Vector3(0,0,16), finalCamera=new THREE.Vector3(0,12,17);
  function tick(now:number){
    if(disposed)return;frame=requestAnimationFrame(tick);
    if(document.hidden)return;
    if(now-lastFrame<30)return;lastFrame=now;
    const time=(now-startTime)/1000, scroll=window.scrollY, phases=currentPhases();
    const {crack,burst,meadow}=phases;
    const moving=eggs.some(e=>e.collected&&now-e.collectedAt<1100);
    if(reduced&&lastScroll===scroll&&lastCount===lastRenderedCount&&!moving&&lastMeadow===meadow)return;
    lastScroll=scroll;lastMeadow=meadow;lastRenderedCount=lastCount;
    mount.style.pointerEvents=meadow>.95?'auto':'none';
    const aspect=width/height;
    // Preserve the full meadow on narrow screens, rather than cropping collectible eggs.
    const finalDistance=aspect<.9?1/aspect:1;
    finalCamera.set(0,12*finalDistance,17*finalDistance);
    camera.position.lerpVectors(initialCamera,finalCamera,meadow);
    target.set(0,0,0);camera.lookAt(target);camera.updateMatrixWorld();
    landscape.visible=meadow>.001;
    landscape.position.y=-8*(1-meadow);
    if(grassMaterial.userData.shader)grassMaterial.userData.shader.uniforms.uTime.value=reduced?0:time;
    giant.visible=burst<.999&&meadow<.8;
    giant.position.set(0,1.65,0);
    giant.rotation.set(0,reduced?0:Math.sin(time*.3)*.08,crack*(1-burst)*(reduced?0:Math.sin(time*20)*.025));
    const separation=crack*.07+burst*4.5;
    shellTop.position.set(-burst*2.6,separation,0);shellBottom.position.set(burst*2.6,-separation,0);
    shellTop.rotation.z=burst*1.3;shellBottom.rotation.z=-burst*1.3;
    giant.scale.setScalar(1.15*(1-burst*.2));
    const spreadWidth=16*Math.tan(THREE.MathUtils.degToRad(17.5))*aspect;
    eggs.forEach(egg=>{
      const {id,mesh}=egg;
      mesh.visible=burst>.015||meadow>.1;
      const a=id/EGG_COUNT*Math.PI*2;
      const tiny=.03+burst*.3;
      let scale=tiny;
      // One continuous set of eggs: contained, bursting, drifting, then landing.
      const drift=clamp((scroll/height-1.15)*.18);
      const orbitX=Math.cos(a)*(1.7+seed(id+81)*2.7)*Math.min(1,spreadWidth/4.7);
      const orbitY=Math.sin(a)*(2+seed(id+37)*2);
      const scatterX=orbitX*burst+(reduced?0:Math.sin(time*.5+id)*.1*burst);
      const scatterY=1.65+(orbitY-1.65)*burst+Math.sin(drift*9+id*2)*drift*.65;
      position.set(scatterX,scatterY,(seed(id+92)-.5)*3*burst);
      const landed=target.copy(egg.destination);landed.y+=landscape.position.y;
      position.lerp(landed,meadow);
      if(meadow>.9&&!reduced&&!egg.collected)position.y+=Math.sin(time*2+id)*.025;
      scale=THREE.MathUtils.lerp(scale,.34,meadow);
      mesh.rotation.set((1-meadow)*burst*(id+time*.25),id*.8+(1-meadow)*time*.15,(1-meadow)*Math.sin(id)*burst);
      if(egg.collected){
        const t=reduced?1:clamp((now-egg.collectedAt)/950), eased=smooth(t);
        const angle=egg.order*2.399;
        const basketTarget=new THREE.Vector3(Math.cos(angle)*.38,.38+Math.floor(egg.order/6)*.17+landscape.position.y,4.4+Math.sin(angle)*.38);
        if(t<1){position.lerpVectors(egg.start,basketTarget,eased);position.y+=Math.sin(Math.PI*t)*2;}
        else position.copy(basketTarget);
        scale=THREE.MathUtils.lerp(.34,.20,eased);mesh.rotation.set(0,id*.8,Math.sin(id)*.45);
      } else if(hovered===id&&meadow>.95){scale*=1.12;position.y+=.1;}
      mesh.position.copy(position);mesh.scale.setScalar(scale);
    });
    renderer.render(scene,camera);
  }
  frame=requestAnimationFrame(tick);
  return {collect,reset,dispose(){
    disposed=true;cancelAnimationFrame(frame);observer.disconnect();window.removeEventListener('resize',measure);media.removeEventListener('change',onReduced);
    renderer.domElement.removeEventListener('pointermove',move);renderer.domElement.removeEventListener('pointerdown',down);renderer.domElement.removeEventListener('pointerup',up);renderer.domElement.removeEventListener('webglcontextlost',contextLost);
    const geometries=new Set<THREE.BufferGeometry>(),mats=new Set<THREE.Material>();scene.traverse(object=>{if(object instanceof THREE.Mesh){geometries.add(object.geometry);for(const mat of Array.isArray(object.material)?object.material:[object.material])mats.add(mat);}});
    geometries.forEach(g=>g.dispose());mats.forEach(m=>m.dispose());envTarget.dispose();renderer.dispose();renderer.domElement.remove();
  }};
}
