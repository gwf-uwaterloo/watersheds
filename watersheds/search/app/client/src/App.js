import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, useMap, Polyline, Polygon } from 'react-leaflet';
import { Layout, Input, List, notification } from 'antd';
import './App.css';

const { Sider } = Layout;
const { Search } = Input;

function riverColor(color) {
  if (color === 1) return '#10281c';
  if (color === 2) return '#183c29';
  if (color === 3) return '#2a6847';
  if (color === 4) return '#3c9566';
  if (color >= 5) return '#77b594';
}

function Rivers({results, selected}) {
  const map = useMap();
  
  useEffect(() => {
    if (results && results.length > selected) {
      map.flyToBounds(results[selected].bounds, {padding: [11, 11]});
    }
  }, [selected, results]);
  
  if (!results) return <></>;
  return (
    <>
      {results[selected]?.basin_geometry?.map(poly => <Polygon positions={poly} pathOptions={{ color: '#66a9c9', weight: 0.5, fillOpacity: 0.1 }}/>)}
      {results[selected]?.geometry?.map(line => <Polyline positions={line[0]} pathOptions={{ color: riverColor(line[1][1]), weight: 1.5 }}/>)}
    </>
  );
}

const openNotificationWithIcon = type => {
  notification[type]({
    message: 'Error fetching request',
  });
};

function App() {
  const [results, setResults] = useState();
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(false);

  async function onSearch(value) {
    setLoading(true);
    
    try {
      const response = await fetch(process.env.REACT_APP_BACKEND_ENDPOINT, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          searchText: value
        })
      });
      const data = await response.json();
      
      console.log(data);
      setResults(data);
      setSelected(0);
      setLoading(false);
    
    } catch (err) {
      openNotificationWithIcon('error');
      setLoading(false);
    }
  }

  useEffect(() => {
    window.dispatchEvent(new Event('resize'));
  })

  return (
    <div className="App">
      <Layout style={{ minHeight: "100vh" }}>
        <Sider width={400} theme='light'>
          <Search placeholder="enter river name" onSearch={onSearch} loading={loading} style={{ width: 380, marginRight: 10, marginLeft: 10, marginTop: 20 }} />
          <List
            dataSource={results}
            style={{ margin: 10, maxHeight: "90vh", overflow: "auto" }}
            renderItem={item => (
              <List.Item onClick={() => setSelected(item.key)} style={item.key === selected ? {backgroundColor: 'gainsboro'} : {}}>
                <List.Item.Meta
                  title={item.contents}
                  description={item.description}
                  style={{ margin: 10 }}
                />
              </List.Item>
            )}
          />
        </Sider>
        <Layout className="site-layout">
          <MapContainer center={[43.4643, -80.5204]} zoom={13} >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <Rivers results={results} selected={selected}/>
          </MapContainer>
        </Layout>
      </Layout>
    </div>
  );
}

export default App;
