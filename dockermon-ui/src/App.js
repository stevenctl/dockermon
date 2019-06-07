import React, {Component} from 'react';
import {Client as Styletron} from 'styletron-engine-atomic';
import {Provider as StyletronProvider} from 'styletron-react';
import {styled} from 'baseui'
import {Select} from 'baseui/select';
import {toaster, ToasterContainer, PLACEMENT} from 'baseui/toast';
import {Table} from 'baseui/table';

import axios from 'axios';

const engine = new Styletron();

const Container = styled('div', {
    maxWidth: '1024px',
    marginLeft: 'auto',
    marginRight: 'auto',
});

const Header = styled('div', {
    display: 'grid',
    gridTemplateColumns: '5fr 1fr',
    gridGap: '24px'
});

const Button = styled('button', ({h, w}) => ({
    backgroundColor: '#4a98ff',
    border: 'none',
    borderRadius: '10px',
    height: h || 'auto',
    width: w || 'auto',
    color: 'white',
    marginBottom: '24px'
}));

export default class App extends Component {
    constructor(props) {
        super(props);
        this.state = {
            containerNames: [],
            selectedContainer: null,
            traffic: {},
            loadingData: false
        };
    }

    componentWillMount() {
        this.loadContainers()
    }

    loadContainers() {
        axios.get("/containers").then((r) => {
            const names = r.data;
            const currentSelected = this.state.selectedContainer && this.state.selectedContainer.v;
            const selectedContainer = names.includes(currentSelected)
                ? this.state.selectedContainer
                : null;

            const containerNames = names.map(n => ({v: n}));

            this.setState({containerNames, selectedContainer})
        });

        const ltd = this.loadTrafficData.bind(this);

        axios.get("/monitored").then((r) => {
            this.setState({
                selectedContainer: {v: r.data}
            });
            ltd()
        })
    }

    loadTrafficData() {
        axios.get("/traffic").then((r) => {
            this.setState({traffic: r.data, loadingData: false})
        }).catch((e) => {
            toaster.negative('An error occurred fetching traffic data')
        })

    }

    selectContainer(e) {
        this.setState({
            selectedContainer: e.option
        });

        axios.put('/monitored', e.option.v).then((r) => {
            toaster.info(r.data)
            this.loadTrafficData();
        }).catch((e) => {
            toaster.negative('An error occured when attempting to start monitor for ' + e.option.v)
        })
    }

    getTableData() {
        return Object.keys(this.state.traffic)
            .map((containerPair) => [
                containerPair,
                this.state.traffic[containerPair].join(", ")
            ])
    }

    render() {
        return (
            <StyletronProvider value={engine}>
                <ToasterContainer placement={PLACEMENT.bottomRight}/>
                <Container>
                    <Header>
                        <Select
                            options={this.state.containerNames}
                            labelKey="v"
                            valueKey="v"
                            value={this.state.selectedContainer}
                            onChange={this.selectContainer.bind(this)}
                        />
                        <Button h="100%" onClick={this.loadContainers.bind(this)}>Refresh</Button>
                    </Header>
                    <br/>

                    <Button h="40px" w="100%" onClick={this.loadTrafficData.bind(this)}>Load Data</Button>
                    <br/>
                    {!this.state.loadingData && <Table
                        columns={['Containers', 'Ports']}
                        data={this.getTableData()}
                    />}
                    {this.state.loadingData &&
                    <div>there is a spinner here</div>
                    }
                </Container>
            </StyletronProvider>
        );
    }
}

