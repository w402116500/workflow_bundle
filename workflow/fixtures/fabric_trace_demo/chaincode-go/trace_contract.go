package main

import "github.com/hyperledger/fabric-contract-api-go/contractapi"

type SmartContract struct {
    contractapi.Contract
}

func (s *SmartContract) CreateBatch(ctx contractapi.TransactionContextInterface, batchID string) error {
    return nil
}

func (s *SmartContract) TransferBatch(ctx contractapi.TransactionContextInterface, batchID string, target string) error {
    return nil
}

func (s *SmartContract) QueryBatch(ctx contractapi.TransactionContextInterface, batchID string) (string, error) {
    return batchID, nil
}
