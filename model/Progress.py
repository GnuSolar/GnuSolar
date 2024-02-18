#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# Project Progress

import os

from model.PvProject import *
from model.Positions import *

from Config import Config

class Progress:
    
    def __init__(self):
        
        self.inquiryReceived = None         # Anfrage erhalten
        self.roofMeasure = None
        self.roofMeasured = None
        self.quote1Sent = None
        self.quote2Sent = None
        self.quote3Sent = None
        self.quote4Sent = None
        self.orderReceived = None           # Auftrag erhalten
        self.orderRejected = None           # Auftrag nicht erhalten
        self.tagSent = None                 # Anschlussgesuch
        self.tagReceived = None
        self.iaSent = None                  # Installationsanzeige
        self.iaReceived = None
        self.bauSent = None                 # Solarmeldung/Baubegsuch
        self.bauReceived = None
        
        self.partialInvoiceSent = None      # Akontorechnung
        self.partialInvoiceReceived = None
        self.partialInvoice2Sent = None      # Akontorechnung 2
        self.partialInvoice2Received = None
        self.materialOrdered = None
        self.materialReceived = None
        self.constructionStart = None
        self.constructionSort = None        # Fake date, for the construction order, defaults to orderReceived
        self.constructionFixed = False      # The construction date can not be moved
        self.launch = None
        self.documentationCreated = None
        self.documentationPlaced = None
        self.finalInvoiceSent = None        # Schlussrechnung verschickt
        self.finalInvoiceReceived = None    # Schlussrechnung bezahlt

        self.siNaDcOrdered = None           # Sicherheitsnachweis DC (M+PP)
        self.siNaDcReceived = None

        self.siNaAcOrdered = None           # Sicherheitsnachweis AC
        self.siNaAcReceived = None

        self.eivComplete = None             # Förderung komplett
        self.eivPayed = None                # Förderung ausbezahlt
        
        self.archived = None                # Projekt archiviert

        self.inactiv = None                # Projekt inaktiv

    # returns state of the project:
    #  activ: Something needs to be done at some point
    #  inactiv: Project will probably be built or not nothing to be done
    #  archived: everything said and done
    #  rejected: project will never be built by us
    
    def getState(self):
        if self.orderRejected:
            return "9 - rejected " + self.orderRejected
        
        # manuell archiviert
        if self.archived:
            return "8 - archived " + self.archived + " manu"

        # EIV ausbezahlt und Schlussrechnung bezahlt => archiviert
        if self.eivPayed and self.finalInvoiceReceived:
            return "8 - archived " + self.eivPayed + " auto"

        # Auftrag abgeschlossen
        if self.eivPayed:
            return "7.2 - EIV payed " + self.eivPayed

        if self.eivComplete:
            return "7.1 - EIV complete " + self.eivComplete

        if self.launch:
            return "6 - in Betrieb " + self.launch
                
        # Auftrag erhalten und noch nicht abgeschlossen => aktiv
        if self.orderReceived:
            return "5 - building " + self.orderReceived
        
        # Auftrag noch nicht erhalten und letzte Aktion nicht älter als
        # 3? Monate => aktiv
        lastQuote = "2000-01-01"
        if self.quote1Sent and self.quote1Sent > lastQuote:
            lastQuote = self.quote1Sent
        if self.quote2Sent and self.quote2Sent > lastQuote:
            lastQuote = self.quote2Sent
        if self.quote3Sent and self.quote3Sent > lastQuote:
            lastQuote = self.quote3Sent
        if self.quote4Sent and self.quote4Sent > lastQuote:
            lastQuote = self.quote4Sent
        
        if lastQuote != "2000-01-01":
            return "4 - quoted " + lastQuote

        if self.inquiryReceived:
            return "3 - lead " + self.inquiryReceived
             
        return "1 - nothing"

    # returns what to do for the project sortable by Importance
    def getToDo(self):
        if not self.launch:
            if self.inquiryReceived and not self.quote1Sent:
                return "2 - quote"

            if self.orderReceived and not self.tagSent:
                return "3 - send TAG"

            if self.orderReceived and not self.bauSent:
                return "3 - send Bau"
            
            if not self.tagReceived and self.tagSent:
                return "4 - check TAG"

            if not self.bauReceived and self.bauSent:
                return "4 - check Bau"

            if not self.iaReceived and self.iaSent:
                return "4 - check IA"

        """
        TODO: financel stuff
        if not self.partialInvoiceReceived and self.partialInvoiceSent:
            return "4 - check partialInvoice"

        if not self.finalInvoiceReceived and self.finalInvoiceSent:
            return "4 - check finalInvoice"
        """
        
        if not self.siNaDcReceived and self.siNaDcOrdered:
            return "6 - check siNaDc"
        
        if not self.siNaAcReceived and self.siNaAcOrdered:
            return "6 - check siNaDc"
 
        if not self.orderReceived:
            return "1 - wait customer"
        
        return "0 - I dunno"

    # constructionSort defaults to orderReceived
    def getConstructionSort(self):
        if not self.constructionSort:
            self.constructionSort = self.orderReceived
        return self.constructionSort

