import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from 'three';
import { EGG_COUNT, collectEgg, meadowPosition, scrollPhases } from '../components/egg/game';
import { eggGeometry } from '../components/egg/scene';

test('collection counts each egg once, rejects invalid IDs, and can reach completion', () => {
  let ids:number[]=[];
  for(let id=0;id<EGG_COUNT;id++) {ids=collectEgg(ids,id);ids=collectEgg(ids,id);}
  assert.equal(ids.length,EGG_COUNT);
  for(const id of [-1,18,NaN,1.5]) assert.deepEqual(collectEgg(ids,id),ids);
  assert.deepEqual(collectEgg([],0),[0]);
});
test('scroll phases start closed, crack before the burst, and finish at the meadow', () => {
  assert.deepEqual(scrollPhases(0,800,7000),{crack:0,burst:0,meadow:0});
  const cracking=scrollPhases(300,800,7000);assert.ok(cracking.crack>0);assert.equal(cracking.burst,0);
  const scattered=scrollPhases(1500,800,7000);assert.equal(scattered.burst,1);assert.equal(scattered.meadow,0);
  assert.equal(scrollPhases(7000,800,7000).meadow,1);
  assert.deepEqual(scrollPhases(0,800,7000),{crack:0,burst:0,meadow:0});
});
test('shell halves have exactly matching jagged rims with outward normals', () => {
  const top=eggGeometry('top'),bottom=eggGeometry('bottom');
  const a=top.attributes.position,b=bottom.attributes.position;
  for(let i=0;i<65;i++) for(let axis=0;axis<3;axis++) {
    assert.ok(Math.abs(a.array[(32*65+i)*3+axis]-b.array[i*3+axis])<1e-6);
  }
  const point=new THREE.Vector3().fromBufferAttribute(a,10*65);
  const normal=new THREE.Vector3().fromBufferAttribute(top.attributes.normal,10*65);
  assert.ok(point.dot(normal)>0,'surface faces outward');
  top.dispose();bottom.dispose();
});
test('all 18 eggs are separate and visible in portrait and desktop meadow cameras', () => {
  const positions=Array.from({length:EGG_COUNT},(_,i)=>new THREE.Vector3(...meadowPosition(i)));
  for(let i=0;i<positions.length;i++)for(let j=i+1;j<positions.length;j++)assert.ok(positions[i].distanceTo(positions[j])>.9);
  for(const [width,height] of [[375,812],[768,1024],[1440,900]]) {
    const aspect=width/height,factor=aspect<.9?1/aspect:1;
    const camera=new THREE.PerspectiveCamera(35,aspect,.1,150);camera.position.set(0,12*factor,17*factor);camera.lookAt(0,0,0);camera.updateMatrixWorld();
    for(const p of positions){const screen=p.clone().project(camera);assert.ok(Math.abs(screen.x)<.85&&Math.abs(screen.y)<.72&&screen.z<1,`${width}px egg remains in view`);}
  }
});
