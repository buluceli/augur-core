#!/usr/bin/env python

from __future__ import division
import os
import sys
import iocapture
import ethereum.tester
from decimal import *
import utils

shareTokenContractTranslator = ethereum.abi.ContractTranslator('[{"constant": false, "type": "function", "name": "allowance(address,address)", "outputs": [{"type": "int256", "name": "out"}], "inputs": [{"type": "address", "name": "owner"}, {"type": "address", "name": "spender"}]}, {"constant": false, "type": "function", "name": "approve(address,uint256)", "outputs": [{"type": "int256", "name": "out"}], "inputs": [{"type": "address", "name": "spender"}, {"type": "uint256", "name": "value"}]}, {"constant": false, "type": "function", "name": "balanceOf(address)", "outputs": [{"type": "int256", "name": "out"}], "inputs": [{"type": "address", "name": "address"}]}, {"constant": false, "type": "function", "name": "changeTokens(int256,int256)", "outputs": [{"type": "int256", "name": "out"}], "inputs": [{"type": "int256", "name": "trader"}, {"type": "int256", "name": "amount"}]}, {"constant": false, "type": "function", "name": "createShares(address,uint256)", "outputs": [{"type": "int256", "name": "out"}], "inputs": [{"type": "address", "name": "owner"}, {"type": "uint256", "name": "fxpValue"}]}, {"constant": false, "type": "function", "name": "destroyShares(address,uint256)", "outputs": [{"type": "int256", "name": "out"}], "inputs": [{"type": "address", "name": "owner"}, {"type": "uint256", "name": "fxpValue"}]}, {"constant": false, "type": "function", "name": "getDecimals()", "outputs": [{"type": "int256", "name": "out"}], "inputs": []}, {"constant": false, "type": "function", "name": "getName()", "outputs": [{"type": "int256", "name": "out"}], "inputs": []}, {"constant": false, "type": "function", "name": "getSymbol()", "outputs": [{"type": "int256", "name": "out"}], "inputs": []}, {"constant": false, "type": "function", "name": "modifySupply(int256)", "outputs": [{"type": "int256", "name": "out"}], "inputs": [{"type": "int256", "name": "amount"}]}, {"constant": false, "type": "function", "name": "setController(address)", "outputs": [{"type": "int256", "name": "out"}], "inputs": [{"type": "address", "name": "newController"}]}, {"constant": false, "type": "function", "name": "suicideFunds(address)", "outputs": [], "inputs": [{"type": "address", "name": "to"}]}, {"constant": false, "type": "function", "name": "totalSupply()", "outputs": [{"type": "int256", "name": "out"}], "inputs": []}, {"constant": false, "type": "function", "name": "transfer(address,uint256)", "outputs": [{"type": "int256", "name": "out"}], "inputs": [{"type": "address", "name": "to"}, {"type": "uint256", "name": "value"}]}, {"constant": false, "type": "function", "name": "transferFrom(address,address,uint256)", "outputs": [{"type": "int256", "name": "out"}], "inputs": [{"type": "address", "name": "from"}, {"type": "address", "name": "to"}, {"type": "uint256", "name": "value"}]}, {"inputs": [{"indexed": true, "type": "address", "name": "owner"}, {"indexed": true, "type": "address", "name": "spender"}, {"indexed": false, "type": "uint256", "name": "value"}], "type": "event", "name": "Approval(address,address,uint256)"}, {"inputs": [{"indexed": true, "type": "address", "name": "from"}, {"indexed": true, "type": "address", "name": "to"}, {"indexed": false, "type": "uint256", "name": "value"}], "type": "event", "name": "Transfer(address,address,uint256)"}, {"inputs": [{"indexed": false, "type": "int256", "name": "from"}, {"indexed": false, "type": "int256", "name": "to"}, {"indexed": false, "type": "int256", "name": "value"}, {"indexed": false, "type": "int256", "name": "senderBalance"}, {"indexed": false, "type": "int256", "name": "sender"}, {"indexed": false, "type": "int256", "name": "spenderMaxValue"}], "type": "event", "name": "echo(int256,int256,int256,int256,int256,int256)"}]')

def test_TakeOrder(contracts):
    t = contracts._ContractLoader__tester
    def test_publicTakeAskOrder():
        global shareTokenContractTranslator
        outcomeShareContractWrapper = utils.makeOutcomeShareContractWrapper(contracts)
        contracts._ContractLoader__state.mine(1)
        fxpEtherDepositValue = utils.fix(100)
        assert(contracts.cash.publicDepositEther(value=fxpEtherDepositValue, sender=t.k1) == 1), "publicDepositEther to account 1 should succeed"
        assert(contracts.cash.publicDepositEther(value=fxpEtherDepositValue, sender=t.k2) == 1), "publicDepositEther to account 2 should succeed"
        contracts._ContractLoader__state.mine(1)
        orderType = 2                   # ask
        fxpAmount = utils.fix(1)
        fxpPrice = utils.fix("1.6")
        outcomeID = 2
        tradeGroupID = 42
        eventID = utils.createBinaryEvent(contracts)
        marketID = utils.createMarket(contracts, eventID)
        assert(contracts.cash.approve(contracts.makeOrder.address, utils.fix(10), sender=t.k1) == 1), "Approve makeOrder contract to spend cash from account 1"
        assert(contracts.cash.approve(contracts.takeOrder.address, utils.fix(10), sender=t.k2) == 1), "Approve takeOrder contract to spend cash from account 2"
        makerInitialCash = contracts.cash.balanceOf(t.a1)
        takerInitialCash = contracts.cash.balanceOf(t.a2)
        marketInitialCash = contracts.cash.balanceOf(contracts.info.getWallet(marketID))
        with iocapture.capture() as captured:
            orderID = contracts.makeOrder.publicMakeOrder(orderType, fxpAmount, fxpPrice, marketID, outcomeID, tradeGroupID, sender=t.k1)
            logged = captured.stdout
        logMakeOrder = utils.parseCapturedLogs(logged)[-1]
        assert(logMakeOrder["_event_type"] == "MakeOrder"), "Should emit a MakeOrder event"
        assert(orderID != 0), "Order ID should be non-zero"
        contracts._ContractLoader__state.mine(1)
        fxpAmountTakerWants = int(fxpAmount / 10)
        t.gas_price = 5
        try:
            raise Exception(contracts.takeOrder.publicTakeOrder(orderID, orderType, marketID, outcomeID, fxpAmountTakerWants, sender=t.k2))
        except Exception as exc:
            assert(isinstance(exc, ethereum.tester.TransactionFailed)), "a call that throws should actually throw the transaction so it fails, tx.gasprice check in orders isn't working"
        t.gas_price = 1
        with iocapture.capture() as captured:
            fxpAmountRemaining = contracts.takeOrder.publicTakeOrder(orderID, orderType, marketID, outcomeID, fxpAmountTakerWants, sender=t.k2)
            logged = captured.stdout
        logTakeOrder = utils.parseCapturedLogs(logged)[-1]
        assert(logTakeOrder["_event_type"] == "TakeAskOrder"), "Should emit a TakeAskOrder event"
        assert(logTakeOrder["fxpPrice"] == fxpPrice), "Logged fxpPrice should be " + str(fxpPrice)
        assert(logTakeOrder["fxpAmount"] == fxpAmountTakerWants), "Logged fxpAmount should be " + str(fxpAmountTakerWants)
        assert(logTakeOrder["fxpAskerSharesFilled"] == 0), "Logged fxpAskerSharesFilled should be 0"
        assert(logTakeOrder["fxpAskerMoneyFilled"] == fxpAmountTakerWants), "Logged fxpAskerMoneyFilled should be " + str(fxpAmountTakerWants)
        assert(logTakeOrder["fxpBidderMoneyFilled"] == fxpAmountTakerWants), "Logged fxpBidderMoneyFilled should be " + str(fxpAmountTakerWants)
        assert(int(logTakeOrder["orderID"], 16) == orderID), "Logged orderID should be " + str(orderID)
        assert(logTakeOrder["outcome"] == outcomeID), "Logged outcome should be " + str(outcomeID)
        assert(int(logTakeOrder["market"], 16) == marketID), "Logged market should be " + str(marketID)
        assert(int(logTakeOrder["owner"], 16) == long(t.a1.encode("hex"), 16)), "Logged owner should be account 1"
        assert(int(logTakeOrder["sender"], 16) == long(t.a2.encode("hex"), 16)), "Logged sender should be account 2"
        assert(logTakeOrder["timestamp"] == contracts._ContractLoader__state.block.timestamp), "Logged timestamp should match the current block timestamp"
        assert(fxpAmountRemaining == 0), "Amount remaining should be 0"
    def test_publicTakeBidOrder():
        global shareTokenContractTranslator
        outcomeShareContractWrapper = utils.makeOutcomeShareContractWrapper(contracts)
        contracts._ContractLoader__state.mine(1)
        fxpEtherDepositValue = utils.fix(100)
        assert(contracts.cash.publicDepositEther(value=fxpEtherDepositValue, sender=t.k1) == 1), "publicDepositEther to account 1 should succeed"
        assert(contracts.cash.publicDepositEther(value=fxpEtherDepositValue, sender=t.k2) == 1), "publicDepositEther to account 2 should succeed"
        contracts._ContractLoader__state.mine(1)
        orderType = 1 # bid
        fxpAmount = utils.fix(1)
        fxpPrice = utils.fix("1.6")
        outcomeID = 2
        tradeGroupID = 42
        eventID = utils.createBinaryEvent(contracts)
        marketID = utils.createMarket(contracts, eventID)
        assert(contracts.cash.approve(contracts.makeOrder.address, utils.fix(10), sender=t.k1) == 1), "Approve makeOrder contract to spend cash from account 1"
        assert(contracts.cash.approve(contracts.takeOrder.address, utils.fix(10), sender=t.k2) == 1), "Approve takeOrder contract to spend cash from account 2"
        fxpAllowance = utils.fix(10)
        outcomeShareContract = contracts.markets.getOutcomeShareContract(marketID, outcomeID)
        abiEncodedData = shareTokenContractTranslator.encode("approve", [contracts.takeOrder.address, fxpAllowance])
        assert(int(contracts._ContractLoader__state.send(t.k2, outcomeShareContract, 0, abiEncodedData).encode("hex"), 16) == 1), "Approve takeOrder contract to spend shares from the user's account (account 2)"
        assert(outcomeShareContractWrapper.allowance(outcomeShareContract, t.a2, contracts.takeOrder.address) == fxpAllowance), "takeOrder contract's allowance should be equal to the amount approved"
        makerInitialCash = contracts.cash.balanceOf(t.a1)
        takerInitialCash = contracts.cash.balanceOf(t.a2)
        marketInitialCash = contracts.cash.balanceOf(contracts.info.getWallet(marketID))
        # place a bid order (escrow cash)
        with iocapture.capture() as captured:
            orderID = contracts.makeOrder.publicMakeOrder(orderType, fxpAmount, fxpPrice, marketID, outcomeID, tradeGroupID, sender=t.k1)
            logged = captured.stdout
        logMakeOrder = utils.parseCapturedLogs(logged)[-1]
        assert(logMakeOrder["_event_type"] == "MakeOrder"), "Should emit a MakeOrder event"
        assert(orderID != 0), "Order ID should be non-zero"
        contracts._ContractLoader__state.mine(1)
        fxpAmountTakerWants = int(fxpAmount / 10)
        assert(contracts.cash.balanceOf(contracts.info.getWallet(marketID)) == utils.fix("0.6")), "Market's cash balance should be (price - 1)*amount"
        with iocapture.capture() as captured:
            fxpAmountRemaining = contracts.takeOrder.publicTakeOrder(orderID, orderType, marketID, outcomeID, fxpAmountTakerWants, sender=t.k2)
            logged = captured.stdout
        logTakeOrder = utils.parseCapturedLogs(logged)[-1]
        assert(logTakeOrder["_event_type"] == "TakeBidOrder"), "Should emit a TakeBidOrder event"
        assert(logTakeOrder["fxpPrice"] == fxpPrice), "Logged fxpPrice should be " + str(fxpPrice)
        assert(logTakeOrder["fxpAmount"] == fxpAmountTakerWants), "Logged fxpAmount should be " + str(fxpAmountTakerWants)
        assert(logTakeOrder["fxpAskerSharesFilled"] == 0), "Logged fxpAskerSharesFilled should be 0"
        assert(logTakeOrder["fxpAskerMoneyFilled"] == fxpAmountTakerWants), "Logged fxpAskerMoneyFilled should be " + str(fxpAmountTakerWants)
        assert(logTakeOrder["fxpBidderSharesFilled"] == 0), "Logged fxpBidderSharesFilled should be 0"
        assert(logTakeOrder["fxpBidderMoneyFilled"] == fxpAmountTakerWants), "Logged fxpBidderMoneyFilled should be " + str(fxpAmountTakerWants)
        assert(int(logTakeOrder["orderID"], 16) == orderID), "Logged orderID should be " + str(orderID)
        assert(logTakeOrder["outcome"] == outcomeID), "Logged outcome should be " + str(outcomeID)
        assert(int(logTakeOrder["market"], 16) == marketID), "Logged market should be " + str(marketID)
        assert(int(logTakeOrder["owner"], 16) == long(t.a1.encode("hex"), 16)), "Logged owner should be account 1"
        assert(int(logTakeOrder["sender"], 16) == long(t.a2.encode("hex"), 16)), "Logged sender should be account 2"
        assert(logTakeOrder["timestamp"] == contracts._ContractLoader__state.block.timestamp), "Logged timestamp should match the current block timestamp"
        assert(fxpAmountRemaining == 0), "Amount remaining should be 0"
    test_publicTakeAskOrder()
    test_publicTakeBidOrder()

if __name__ == '__main__':
    ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    sys.path.insert(0, os.path.join(ROOT, "upload_contracts"))
    from upload_contracts import ContractLoader
    contracts = ContractLoader(os.path.join(ROOT, "src"), "controller.se", ["mutex.se", "cash.se", "repContract.se"])
    test_TakeOrder(contracts)
