import React, {useState} from 'react'; import {createRoot} from 'react-dom/client'; import './style.css';
function App(){
 const [q,setQ]=useState(''),[items,setItems]=useState([]),[error,setError]=useState('');
 async function search(e){e.preventDefault();setError('');try{
  const r=await fetch(`http://localhost:8000/questions?q=${encodeURIComponent(q)}`);
  if(!r.ok) throw new Error('Falha na consulta'); const d=await r.json();setItems(d.items||[]);
 }catch(err){setError('Não foi possível consultar a API. Verifique se os serviços estão ativos.');}}
 return <main><h1>Acervo ENADE</h1><p>Pesquisa distribuída de questões, provas e gabaritos.</p>
 <form onSubmit={search}><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Pesquise por tema, competência ou enunciado"/><button>Buscar</button></form>
 {error&&<p role="alert">{error}</p>}<section>{items.map(x=><article key={x.id}><small>{x.question.course} · {x.question.year||'Ano não informado'} · {x.question.source_pdf}, pág. {x.question.source_page}</small><p>{x.highlight?.statement?.[0] ? <span dangerouslySetInnerHTML={{__html:x.highlight.statement[0]}}/> : x.question.statement}</p></article>)}</section>
 </main>}
createRoot(document.getElementById('root')).render(<App/>);
