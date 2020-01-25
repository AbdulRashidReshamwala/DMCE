pragma solidity 0.6.0;
pragma experimental ABIEncoderV2;

contract SupplyChain{
    
    address public superuser;
    uint nodeCount;
    uint batchCount;
    uint[] batchIds;
    address[] nodeIds;
    
    
    // total batches and Nodes
    mapping(uint => Batch) totalBatches;
    mapping(address => Node ) totalNodes;
    
    
    // location datastruct
    struct Location{
        string lat;
        string lon;
    }
    
    // Batch struct
    struct Batch{
        uint id;
        uint stopCount;
        string drug;
        Stop[] stops;
        bool shipping;
        address destination;
    }
    
    struct Stop{
        address nodeAddress;
        string arrivalTime;
        string departureTime;
    }
    
    struct Node{
        // uint id;
        uint noNodeBatches;
        bool exists;
        string name;
        uint level;
        address id;
        Location location;
        uint[] nodeBatches;
    }
    
    constructor(address _owner) public{
        superuser = _owner;
        nodeCount = 0;
        batchCount = 0;
    }
    
    function addNode(string memory _name, uint _level, string memory _lat,string memory _lon,address _id) public{
        assert(msg.sender == superuser);
        assert(totalNodes[_id].exists == false);
        totalNodes[_id].name = _name;
        totalNodes[_id].id = _id;
        totalNodes[_id].level = _level;
        totalNodes[_id].location.lat= _lat;
        totalNodes[_id].location.lon = _lon;
        totalNodes[_id].exists = true;
        totalNodes[_id].noNodeBatches = 0;
        nodeIds.push(_id);
        nodeCount += 1;
    }
    
    function viewNode(address _id) public view returns(string memory,address,uint,uint[] memory) {
        assert(totalNodes[_id].exists);
        return(totalNodes[_id].name,totalNodes[_id].id,totalNodes[_id].level,totalNodes[_id].nodeBatches);
    }
    
    
    function addBatch(address _rootnode, string memory _name,string memory _time) public {
        // Batch storage _batch = totalBatches[batchCount];
        // _batch.stops[0]=Stop(_rootnode,0,0);
        totalBatches[batchCount].drug = _name;
        totalBatches[batchCount].id = batchCount+1;
        totalBatches[batchCount].stops[0]=Stop(_rootnode,_time,'null');
        totalBatches[batchCount].stopCount += 1;
        totalBatches[batchCount].shipping = false;
        
        totalNodes[_rootnode].nodeBatches.push(batchCount);
        
        totalNodes[_rootnode].noNodeBatches += 1;
        batchCount += 1;
    }
    
    function viewBatch(uint _id) public view returns(string memory,uint,bool,address,uint){
        assert(_id < batchCount);
        return (totalBatches[_id].drug,_id,totalBatches[_id].shipping,totalBatches[_id].destination,totalBatches[_id].stopCount);
    }
    
    function forwardBatch(uint _id,address _destination,string memory _time) public{
        assert(totalNodes[_destination].exists);
        totalBatches[_id].destination = _destination;
        totalBatches[_id].shipping = true;
        totalBatches[_id].stops[totalBatches[_id].stopCount].departureTime = _time; 
    }
    
    function acceptBatch(uint _id,string memory _time) public{
        assert(totalBatches[_id].destination == msg.sender);
        totalBatches[_id].shipping = false;
        totalBatches[_id].stops.push(Stop(msg.sender,_time,'null'));
        totalBatches[_id].stopCount +=1;
        totalBatches[_id].destination = address(0);
    }
    
}
